import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Send, ArrowLeft } from 'lucide-react'
import { messagesApi } from '../api/client'
import useAuthStore from '../store/authStore'
import { format } from 'date-fns'
import clsx from 'clsx'

export default function MessagesPage() {
  const { id: convId } = useParams()
  const { user } = useAuthStore()
  const qc = useQueryClient()
  const [text, setText] = useState('')
  const [ws, setWs] = useState(null)
  const [messages, setMessages] = useState([])
  const bottomRef = useRef(null)

  const { data: conversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => messagesApi.getConversations().then((r) => r.data),
  })

  const { data: history } = useQuery({
    queryKey: ['messages', convId],
    queryFn: () => messagesApi.getMessages(convId).then((r) => r.data),
    enabled: !!convId,
  })

  useEffect(() => {
    if (history) setMessages(history)
  }, [history])

  // Connect WebSocket
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) return
    const socket = new WebSocket(`ws://localhost:8000/api/v1/messages/ws?token=${token}`)

    socket.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'new_message' && data.message.conversation_id === convId) {
        setMessages((prev) => [...prev, data.message])
      }
    }
    setWs(socket)
    return () => socket.close()
  }, [convId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = () => {
    if (!text.trim() || !ws) return
    ws.send(JSON.stringify({ type: 'send_message', conversation_id: convId, content: text }))
    setText('')
  }

  const activeConv = conversations?.find((c) => c.id === convId)

  return (
    <div className="page-container py-6">
      <div className="flex h-[calc(100vh-200px)] gap-4">

        {/* Conversation list */}
        <div className={clsx('w-72 flex-shrink-0 flex flex-col gap-1', convId && 'hidden md:flex')}>
          <h2 className="font-display font-bold text-xl text-brand-ink mb-3">Messages</h2>
          {!conversations?.length ? (
            <div className="text-center py-10 text-brand-ink/40">
              <p className="text-3xl mb-2">💬</p>
              <p className="font-body text-sm">No conversations yet</p>
            </div>
          ) : (
            conversations.map((conv) => {
              const other = conv.participants?.find((p) => p.user_id !== user?.id)
              return (
                <Link key={conv.id} to={`/messages/${conv.id}`}
                  className={clsx('flex items-center gap-3 p-3 rounded-xl transition-all',
                    conv.id === convId ? 'bg-brand-orange/10 border border-brand-orange/20' : 'hover:bg-black/5')}>
                  <div className="w-10 h-10 rounded-full bg-brand-ink overflow-hidden flex-shrink-0">
                    {other?.user?.avatar_url
                      ? <img src={other.user.avatar_url} alt="" className="w-full h-full object-cover" />
                      : <div className="w-full h-full flex items-center justify-center text-white font-display font-bold text-sm">
                          {other?.user?.first_name?.[0]}
                        </div>
                    }
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-display font-semibold text-sm truncate">{other?.user?.first_name}</p>
                    <p className="text-xs text-brand-ink/40 font-body truncate">{conv.listing?.title}</p>
                  </div>
                  {conv.unread_count > 0 && (
                    <span className="w-5 h-5 bg-brand-orange rounded-full flex items-center justify-center text-white text-xs font-display font-bold">
                      {conv.unread_count}
                    </span>
                  )}
                </Link>
              )
            })
          )}
        </div>

        {/* Chat area */}
        {convId ? (
          <div className="flex-1 flex flex-col card overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 border-b border-black/5 flex items-center gap-3">
              <Link to="/messages" className="md:hidden text-brand-ink/50 hover:text-brand-ink">
                <ArrowLeft size={18} />
              </Link>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-brand-ink" />
                <div>
                  <p className="font-display font-semibold text-sm">Conversation</p>
                  {activeConv?.listing && (
                    <p className="text-xs text-brand-ink/40 font-mono">{activeConv.listing.title}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.map((msg) => {
                const isMe = msg.sender_id === user?.id
                return (
                  <div key={msg.id} className={clsx('flex', isMe ? 'justify-end' : 'justify-start')}>
                    <div className={clsx(
                      'max-w-xs px-4 py-2.5 rounded-2xl font-body text-sm',
                      isMe
                        ? 'bg-brand-orange text-white rounded-br-sm'
                        : 'bg-black/5 text-brand-ink rounded-bl-sm'
                    )}>
                      <p>{msg.content}</p>
                      <p className={clsx('text-xs mt-1', isMe ? 'text-white/60' : 'text-brand-ink/30')}>
                        {format(new Date(msg.created_at), 'h:mm a')}
                      </p>
                    </div>
                  </div>
                )
              })}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="px-4 py-3 border-t border-black/5 flex items-center gap-3">
              <input
                className="input py-2 text-sm flex-1"
                placeholder="Type a message..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              />
              <button onClick={sendMessage} disabled={!text.trim()}
                className="w-10 h-10 bg-brand-orange rounded-xl flex items-center justify-center
                           hover:bg-orange-600 disabled:opacity-40 transition-colors">
                <Send size={16} className="text-white" />
              </button>
            </div>
          </div>
        ) : (
          <div className="hidden md:flex flex-1 items-center justify-center text-brand-ink/30">
            <div className="text-center">
              <p className="text-5xl mb-3">💬</p>
              <p className="font-display font-semibold">Select a conversation</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}