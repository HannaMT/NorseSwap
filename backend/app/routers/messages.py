"""
LEARN: WebSockets in FastAPI
==============================
FastAPI has native WebSocket support — no separate library needed!

WebSocket vs HTTP:
  - HTTP: Client sends request → server responds → connection closes
  - WebSocket: Connection stays OPEN → both sides can send messages anytime

This is how real-time chat works. When user A sends a message:
  1. Message is saved to DB
  2. Server pushes it to user B's WebSocket connection
  3. User B sees it instantly — no polling needed

Connection manager pattern:
  We keep a dict of active connections {user_id: websocket}
  When a message arrives, we look up the recipient's connection and send it
"""

from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
# app/routers/messages.py
from app.utils.email import send_new_message_email

from app.core.database import get_db, AsyncSessionLocal
from app.core.dependencies import get_current_user, get_verified_user
from app.core.security import decode_token
from app.models.models import (
    User, Conversation, ConversationParticipant, Message
)
from app.schemas.schemas import (
    ConversationCreate, MessageCreate, ConversationResponse, MessageResponse, MessageOnlyResponse
)

router = APIRouter(prefix="/messages", tags=["Messaging"])


# ─── WebSocket Connection Manager ─────────────
class ConnectionManager:
    """
    LEARN: This class manages all active WebSocket connections.
    
    It's a simple in-memory store: { user_id: [websocket, websocket, ...] }
    (A user might have multiple tabs open, so we use a list)
    
    For production scale (multiple servers), you'd use Redis pub/sub instead
    of this in-memory approach. That's the natural upgrade path.
    """

    def __init__(self):
        # LEARN: Dict mapping user_id → list of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        print(f"🔌 WS Connected: {user_id} (total: {len(self.active_connections[user_id])} connections)")

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f"❌ WS Disconnected: {user_id}")

    async def send_to_user(self, user_id: str, data: dict):
        """Send a message to all connections for a specific user"""
        if user_id in self.active_connections:
            dead_connections = []
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead_connections.append(ws)
            # Clean up dead connections
            for ws in dead_connections:
                self.active_connections[user_id].remove(ws)

    def is_online(self, user_id: str) -> bool:
        return user_id in self.active_connections
    


# LEARN: Single manager instance shared across the entire app
manager = ConnectionManager()


# ─── WebSocket Endpoint ────────────────────────
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket,background_tasks: BackgroundTasks):
    """
    LEARN: WebSocket endpoint in FastAPI.
    
    The client connects with:
      const ws = new WebSocket("ws://localhost:8000/api/v1/messages/ws?token=YOUR_JWT")
    
    Then sends JSON messages like:
      ws.send(JSON.stringify({ type: "send_message", conversation_id: "...", content: "Hello!" }))
    
    We can't use Depends() for WebSocket auth (it's not HTTP), so we
    extract the token from query params manually.
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return

    try:
        payload = decode_token(token)
        user_id = payload["user_id"]
    except Exception:
        await websocket.close(code=4001)
        return

    await manager.connect(user_id, websocket)

    try:
        # LEARN: `while True` keeps the connection alive, processing messages as they arrive
        while True:
            # Receive JSON from client
            data = await websocket.receive_json()
            msg_type = data.get("type")

            async with AsyncSessionLocal() as db:
                if msg_type == "send_message":
                   await handle_send_message(db, user_id, data, websocket, background_tasks)
                elif msg_type == "typing_start":
                    await handle_typing(db, user_id, data, is_typing=True)
                elif msg_type == "typing_stop":
                    await handle_typing(db, user_id, data, is_typing=False)
                elif msg_type == "mark_read":
                    await handle_mark_read(db, user_id, data)

    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)


async def handle_send_message(db: AsyncSession, sender_id: str, data: dict, ws: WebSocket,background_tasks: BackgroundTasks):
    conversation_id = data.get("conversation_id")
    content = data.get("content", "").strip()

    if not content or not conversation_id:
        await ws.send_json({"type": "error", "message": "conversation_id and content required"})
        return

    # Verify sender is a participant
    result = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == sender_id,
        )
    )
    if not result.scalar_one_or_none():
        await ws.send_json({"type": "error", "message": "Not a participant"})
        return

    # Save message
    message = Message(conversation_id=conversation_id, sender_id=sender_id, content=content)
    db.add(message)
    await db.flush()

    # Load sender for response
    sender_result = await db.execute(select(User).where(User.id == sender_id))
    sender = sender_result.scalar_one()

    await db.commit()

    message_data = {
        "type": "new_message",
        "message": {
            "id": message.id,
            "conversation_id": conversation_id,
            "content": content,
            "created_at": message.created_at.isoformat(),
            "sender": {
                "id": sender.id,
                "first_name": sender.first_name,
                "last_name": sender.last_name,
                "avatar_url": sender.avatar_url,
            },
        },
    }

    # Get all participants and send to each
    # participants_result = await db.execute(
    #     select(ConversationParticipant.user_id).where(
    #         ConversationParticipant.conversation_id == conversation_id
    #     )
    # )
    participants_result = await db.execute(
        select(ConversationParticipant)
        .options(selectinload(ConversationParticipant.user)) # Eager load user for email
        .where(ConversationParticipant.conversation_id == conversation_id)
    )
    participants = participants_result.scalars().all()

    # participant_ids = [row[0] for row in participants_result.fetchall()]

    # for uid in participant_ids:
    #     await manager.send_to_user(uid, message_data)
    for p in participants:
        # Send real-time WS message to everyone in the chat
        await manager.send_to_user(p.user_id, message_data)

        # 3. Trigger email ONLY for the recipient (not the sender)
        if p.user_id != sender_id:
            background_tasks.add_task(
                send_new_message_email,
                p.user.email,
                p.user.first_name,
                sender.first_name,
                content,
                conversation_id
            )


async def handle_typing(db: AsyncSession, sender_id: str, data: dict, is_typing: bool):
    conversation_id = data.get("conversation_id")
    if not conversation_id:
        return

    # Get sender name
    result = await db.execute(select(User).where(User.id == sender_id))
    sender = result.scalar_one_or_none()
    if not sender:
        return

    # Notify other participants
    participants_result = await db.execute(
        select(ConversationParticipant.user_id).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id != sender_id,
        )
    )
    for row in participants_result.fetchall():
        await manager.send_to_user(row[0], {
            "type": "typing_start" if is_typing else "typing_stop",
            "conversation_id": conversation_id,
            "user_id": sender_id,
            "name": sender.first_name,
        })


async def handle_mark_read(db: AsyncSession, user_id: str, data: dict):
    from datetime import datetime, timezone
    conversation_id = data.get("conversation_id")
    if not conversation_id:
        return

    result = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id,
        )
    )
    participant = result.scalar_one_or_none()
    if participant:
        participant.last_read_at = datetime.now(timezone.utc)
        await db.commit()


# ─── REST Endpoints (fallback for WebSocket) ──

@router.post("/conversations", response_model=dict, status_code=201)
async def get_or_create_conversation(
    body: ConversationCreate,
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    if body.recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself.")

    # Check if conversation already exists
    result = await db.execute(
        select(Conversation)
        .join(ConversationParticipant)
        .where(
            ConversationParticipant.user_id == current_user.id,
            Conversation.listing_id == body.listing_id,
        )
    )
    existing = result.scalars().first()
    if existing:
        # Verify recipient is also in this conversation
        p_result = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == existing.id,
                ConversationParticipant.user_id == body.recipient_id,
            )
        )
        if p_result.scalar_one_or_none():
            return {"id": existing.id, "created": False}

    # Create new conversation
    conversation = Conversation(listing_id=body.listing_id)
    db.add(conversation)
    await db.flush()

    db.add(ConversationParticipant(conversation_id=conversation.id, user_id=current_user.id))
    db.add(ConversationParticipant(conversation_id=conversation.id, user_id=body.recipient_id))

    return {"id": conversation.id, "created": True}


@router.get("/conversations", response_model=List[dict])
async def get_conversations(
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .join(ConversationParticipant)
        .options(
            selectinload(Conversation.participants).selectinload(ConversationParticipant.user),
            selectinload(Conversation.messages),
        )
        .where(ConversationParticipant.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().unique().all()

    response = []
    for conv in conversations:
        last_msg = conv.messages[-1] if conv.messages else None
        participant = next((p for p in conv.participants if p.user_id == current_user.id), None)
        unread = sum(
            1 for m in conv.messages
            if m.sender_id != current_user.id
            and (participant is None or participant.last_read_at is None or m.created_at > participant.last_read_at)
        )
        response.append({
            "id": conv.id,
            "listing_id": conv.listing_id,
            "participants": [
                {"user_id": p.user_id, "first_name": p.user.first_name, "avatar_url": p.user.avatar_url}
                for p in conv.participants
            ],
            "last_message": {"content": last_msg.content, "created_at": last_msg.created_at.isoformat()} if last_msg else None,
            "unread_count": unread,
        })

    return response


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    cursor: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify participant
    result = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a participant.")

    query = (
        select(Message)
        .options(selectinload(Message.sender))
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    messages = result.scalars().all()
    return list(reversed(messages))