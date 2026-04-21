import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, delete

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.models import (
    User,
    Listing,
    ListingImage,
    RentalDetails,
    SaleDetails,
    ServiceDetails,
    Rental,
    ServiceBooking,
    ListingType,
    ListingStatus,
    ListingCondition,
    PricePeriod,
    RentalStatus,
    BookingStatus,
    ServiceCategory,
)

UNIVERSITY = "Northern Kentucky University"
PASSWORD = "Password123!"

IMAGE_MAP = {
    "bike": "/static/images/bike.jpg",
    "calculator": "/static/images/calculator.jpg",
    "camera": "/static/images/camera.jpg",
    "projector": "/static/images/projector.jpg",
    "fridge": "/static/images/fridge.jpg",
    "desk": "/static/images/desk.jpg",
    "textbook": "/static/images/textbook.jpg",
    "monitor": "/static/images/monitor.jpg",
    "lamp": "/static/images/lamp.jpg",
    "controller": "/static/images/controller.jpg",
    "notes": "/static/images/notes.jpg",
    "chair": "/static/images/chair.jpg",
    "tutoring": "/static/images/tutoring.jpg",
    "ride": "/static/images/ride.jpg",
    "photography": "/static/images/photography.jpg",
    "resume": "/static/images/resume.jpg",
    "coding": "/static/images/coding.jpg",
    "guitar": "/static/images/guitar.jpg",
}

DEMO_USERS = [
    {"first_name": "Ava", "last_name": "Morgan", "email": "ava.morgan.demo@nku.edu"},
    {"first_name": "Liam", "last_name": "Carter", "email": "liam.carter.demo@nku.edu"},
    {"first_name": "Maya", "last_name": "Patel", "email": "maya.patel.demo@nku.edu"},
    {"first_name": "Noah", "last_name": "Brooks", "email": "noah.brooks.demo@nku.edu"},
    {"first_name": "Sofia", "last_name": "Reed", "email": "sofia.reed.demo@nku.edu"},
    {"first_name": "Ethan", "last_name": "Price", "email": "ethan.price.demo@nku.edu"},
    {"first_name": "Chloe", "last_name": "Bennett", "email": "chloe.bennett.demo@nku.edu"},
    {"first_name": "Daniel", "last_name": "Flores", "email": "daniel.flores.demo@nku.edu"},
    {"first_name": "Nina", "last_name": "Kim", "email": "nina.kim.demo@nku.edu"},
    {"first_name": "Marcus", "last_name": "Hill", "email": "marcus.hill.demo@nku.edu"},
]

RENTAL_LISTINGS = [
    {
        "owner": 0,
        "title": "Trek Hybrid Bike",
        "description": "Great for getting around campus. Helmet lock included.",
        "category": "Bikes",
        "location": "NKU Student Union",
        "allow_other_campuses": False,
        "tags": ["bike", "commute", "campus"],
        "image_key": "bike",
        "price_per_period": 12.0,
        "price_period": PricePeriod.DAILY,
        "deposit_amount": 40.0,
        "min_rental_days": 1,
    },
    {
        "owner": 1,
        "title": "Mountain Bike Rental",
        "description": "Comfortable bike rental for campus rides and weekend trips.",
        "category": "Bikes",
        "location": "Campus Recreation Center",
        "allow_other_campuses": True,
        "tags": ["bike", "mountain", "rental"],
        "image_key": "bike",
        "price_per_period": 15.0,
        "price_period": PricePeriod.DAILY,
        "deposit_amount": 50.0,
        "min_rental_days": 1,
    },
    {
        "owner": 2,
        "title": "Weekend Commuter Bike",
        "description": "Reliable commuter bike for class, work, and errands.",
        "category": "Bikes",
        "location": "Steely Library",
        "allow_other_campuses": True,
        "tags": ["bike", "commuter", "student"],
        "image_key": "bike",
        "price_per_period": 18.0,
        "price_period": PricePeriod.WEEKLY,
        "deposit_amount": 60.0,
        "min_rental_days": 7,
    },
    {
        "owner": 3,
        "title": "TI-84 Calculator",
        "description": "Perfect for calculus, statistics, and exam prep.",
        "category": "Electronics",
        "location": "Steely Library",
        "allow_other_campuses": False,
        "tags": ["calculator", "math", "exam"],
        "image_key": "calculator",
        "price_per_period": 5.0,
        "price_period": PricePeriod.DAILY,
        "deposit_amount": 15.0,
        "min_rental_days": 1,
    },
    {
        "owner": 4,
        "title": "Scientific Calculator Rental",
        "description": "Affordable calculator rental for quizzes and tests.",
        "category": "Electronics",
        "location": "Science Center",
        "allow_other_campuses": False,
        "tags": ["calculator", "science", "test"],
        "image_key": "calculator",
        "price_per_period": 4.0,
        "price_period": PricePeriod.DAILY,
        "deposit_amount": 10.0,
        "min_rental_days": 1,
    },
    {
        "owner": 5,
        "title": "Canon DSLR Camera",
        "description": "Includes battery, strap, and memory card. Great for campus shoots.",
        "category": "Cameras",
        "location": "Fine Arts Building",
        "allow_other_campuses": True,
        "tags": ["camera", "photo", "media"],
        "image_key": "camera",
        "price_per_period": 22.0,
        "price_period": PricePeriod.DAILY,
        "deposit_amount": 80.0,
        "min_rental_days": 1,
    },
    {
        "owner": 6,
        "title": "Event Camera Rental",
        "description": "Good option for club events, photos, and student projects.",
        "category": "Cameras",
        "location": "Student Union",
        "allow_other_campuses": True,
        "tags": ["camera", "event", "club"],
        "image_key": "camera",
        "price_per_period": 25.0,
        "price_period": PricePeriod.DAILY,
        "deposit_amount": 90.0,
        "min_rental_days": 1,
    },
    {
        "owner": 7,
        "title": "Portable Projector",
        "description": "Great for club presentations or movie nights.",
        "category": "Electronics",
        "location": "Dorm pickup",
        "allow_other_campuses": True,
        "tags": ["projector", "presentation", "events"],
        "image_key": "projector",
        "price_per_period": 18.0,
        "price_period": PricePeriod.DAILY,
        "deposit_amount": 50.0,
        "min_rental_days": 1,
    },
    {
        "owner": 8,
        "title": "Movie Night Projector",
        "description": "Simple projector setup for dorm movie nights and group hangouts.",
        "category": "Electronics",
        "location": "Callahan Hall",
        "allow_other_campuses": True,
        "tags": ["projector", "movie", "dorm"],
        "image_key": "projector",
        "price_per_period": 20.0,
        "price_period": PricePeriod.DAILY,
        "deposit_amount": 55.0,
        "min_rental_days": 1,
    },
    {
        "owner": 9,
        "title": "Mini Fridge",
        "description": "Compact fridge for weekend events or short dorm use.",
        "category": "Furniture",
        "location": "Campbell Hall",
        "allow_other_campuses": False,
        "tags": ["fridge", "dorm", "appliance"],
        "image_key": "fridge",
        "price_per_period": 25.0,
        "price_period": PricePeriod.WEEKLY,
        "deposit_amount": 60.0,
        "min_rental_days": 7,
    },
    {
        "owner": 0,
        "title": "Foldable Study Table",
        "description": "Useful when extra desk space is needed in the dorm.",
        "category": "Furniture",
        "location": "Norse Commons",
        "allow_other_campuses": False,
        "tags": ["desk", "study", "furniture"],
        "image_key": "desk",
        "price_per_period": 10.0,
        "price_period": PricePeriod.WEEKLY,
        "deposit_amount": 20.0,
        "min_rental_days": 7,
    },
    {
        "owner": 1,
        "title": "Compact Study Desk",
        "description": "Small foldable desk for dorm study sessions and laptop work.",
        "category": "Furniture",
        "location": "Dorm pickup",
        "allow_other_campuses": False,
        "tags": ["desk", "compact", "study"],
        "image_key": "desk",
        "price_per_period": 12.0,
        "price_period": PricePeriod.WEEKLY,
        "deposit_amount": 25.0,
        "min_rental_days": 7,
    },
]

SALE_LISTINGS = [
    {
        "owner": 2,
        "title": "Algorithms Textbook",
        "description": "Introduction to Algorithms in solid condition.",
        "category": "Textbooks",
        "location": "Steely Library",
        "allow_other_campuses": True,
        "tags": ["book", "algorithms", "cs"],
        "image_key": "textbook",
        "price": 48.0,
        "condition": ListingCondition.GOOD,
        "is_negotiable": True,
        "quantity": 1,
    },
    {
        "owner": 3,
        "title": "CS Study Materials Bundle",
        "description": "Helpful course materials and reference notes for CS students.",
        "category": "Textbooks",
        "location": "Virtual or library meetup",
        "allow_other_campuses": True,
        "tags": ["cs", "study", "materials"],
        "image_key": "textbook",
        "price": 22.0,
        "condition": ListingCondition.GOOD,
        "is_negotiable": False,
        "quantity": 2,
    },
    {
        "owner": 4,
        "title": "Dell Monitor",
        "description": "24-inch monitor with HDMI cable included.",
        "category": "Electronics",
        "location": "Dorm pickup",
        "allow_other_campuses": False,
        "tags": ["monitor", "desk", "setup"],
        "image_key": "monitor",
        "price": 75.0,
        "condition": ListingCondition.GOOD,
        "is_negotiable": True,
        "quantity": 1,
    },
    {
        "owner": 5,
        "title": "Second Monitor Setup",
        "description": "Great extra monitor for coding, gaming, or productivity.",
        "category": "Electronics",
        "location": "Parking garage pickup",
        "allow_other_campuses": False,
        "tags": ["monitor", "coding", "workspace"],
        "image_key": "monitor",
        "price": 68.0,
        "condition": ListingCondition.GOOD,
        "is_negotiable": True,
        "quantity": 1,
    },
    {
        "owner": 6,
        "title": "Dorm Lamp Set",
        "description": "Warm desk lamp set for study corners and late-night work.",
        "category": "Furniture",
        "location": "Callahan Hall",
        "allow_other_campuses": False,
        "tags": ["lamp", "lighting", "dorm"],
        "image_key": "lamp",
        "price": 20.0,
        "condition": ListingCondition.LIKE_NEW,
        "is_negotiable": False,
        "quantity": 2,
    },
    {
        "owner": 7,
        "title": "LED Desk Lamp",
        "description": "Simple modern desk lamp with cozy light for dorm rooms.",
        "category": "Furniture",
        "location": "Dorm pickup",
        "allow_other_campuses": False,
        "tags": ["lamp", "desk", "light"],
        "image_key": "lamp",
        "price": 15.0,
        "condition": ListingCondition.LIKE_NEW,
        "is_negotiable": False,
        "quantity": 1,
    },
    {
        "owner": 8,
        "title": "PlayStation Controller",
        "description": "Works perfectly with only light wear from normal use.",
        "category": "Gaming Gear",
        "location": "Campus recreation center",
        "allow_other_campuses": True,
        "tags": ["gaming", "controller", "ps"],
        "image_key": "controller",
        "price": 35.0,
        "condition": ListingCondition.GOOD,
        "is_negotiable": True,
        "quantity": 1,
    },
    {
        "owner": 9,
        "title": "Gaming Controller",
        "description": "Extra controller in good shape for casual gaming sessions.",
        "category": "Gaming Gear",
        "location": "Student Union",
        "allow_other_campuses": True,
        "tags": ["controller", "gaming", "console"],
        "image_key": "controller",
        "price": 28.0,
        "condition": ListingCondition.GOOD,
        "is_negotiable": True,
        "quantity": 1,
    },
    {
        "owner": 0,
        "title": "Chemistry Notes",
        "description": "Printed notes and study sheets from last semester.",
        "category": "Textbooks",
        "location": "Science Center",
        "allow_other_campuses": False,
        "tags": ["chemistry", "notes", "study"],
        "image_key": "notes",
        "price": 12.0,
        "condition": ListingCondition.GOOD,
        "is_negotiable": False,
        "quantity": 3,
    },
    {
        "owner": 1,
        "title": "Exam Notes Bundle",
        "description": "Helpful highlighted notes and study pages for exam prep.",
        "category": "Textbooks",
        "location": "Steely Library",
        "allow_other_campuses": False,
        "tags": ["notes", "exam", "study"],
        "image_key": "notes",
        "price": 10.0,
        "condition": ListingCondition.GOOD,
        "is_negotiable": False,
        "quantity": 2,
    },
    {
        "owner": 2,
        "title": "Desk Chair",
        "description": "Comfortable rolling chair for apartment or dorm use.",
        "category": "Furniture",
        "location": "Pickup near parking garage",
        "allow_other_campuses": False,
        "tags": ["chair", "desk", "furniture"],
        "image_key": "chair",
        "price": 55.0,
        "condition": ListingCondition.FAIR,
        "is_negotiable": True,
        "quantity": 1,
    },
    {
        "owner": 3,
        "title": "Ergonomic Chair",
        "description": "Comfortable office chair for long study and coding sessions.",
        "category": "Furniture",
        "location": "Dorm pickup",
        "allow_other_campuses": False,
        "tags": ["chair", "ergonomic", "office"],
        "image_key": "chair",
        "price": 62.0,
        "condition": ListingCondition.GOOD,
        "is_negotiable": True,
        "quantity": 1,
    },
]

SERVICE_LISTINGS = [
    {
        "owner": 4,
        "title": "Calculus Tutoring",
        "description": "Patient tutoring for quizzes, exams, and homework help.",
        "category": "Tutoring",
        "location": "Steely Library",
        "allow_other_campuses": True,
        "tags": ["math", "tutoring", "calculus"],
        "image_key": "tutoring",
        "service_category": ServiceCategory.TUTORING,
        "price_per_hour": 18.0,
        "min_hours": 1,
        "max_hours": 3,
        "skill_level": "Undergraduate STEM",
    },
    {
        "owner": 5,
        "title": "Exam Prep Tutoring",
        "description": "Focused one-on-one prep sessions for STEM exams.",
        "category": "Tutoring",
        "location": "Library study room",
        "allow_other_campuses": True,
        "tags": ["exam", "prep", "tutoring"],
        "image_key": "tutoring",
        "service_category": ServiceCategory.TUTORING,
        "price_per_hour": 20.0,
        "min_hours": 1,
        "max_hours": 2,
        "skill_level": "Exam-focused tutoring",
    },
    {
        "owner": 6,
        "title": "Airport Ride",
        "description": "Affordable rides to CVG for students with luggage.",
        "category": "Rides",
        "location": "NKU campus pickup",
        "allow_other_campuses": True,
        "tags": ["ride", "airport", "transport"],
        "image_key": "ride",
        "service_category": ServiceCategory.RIDES,
        "price_per_hour": 22.0,
        "min_hours": 1,
        "max_hours": 2,
        "skill_level": "Licensed driver",
    },
    {
        "owner": 7,
        "title": "Campus Pickup Service",
        "description": "Short campus and nearby rides for students and luggage.",
        "category": "Rides",
        "location": "Student Union",
        "allow_other_campuses": True,
        "tags": ["ride", "pickup", "student"],
        "image_key": "ride",
        "service_category": ServiceCategory.RIDES,
        "price_per_hour": 18.0,
        "min_hours": 1,
        "max_hours": 2,
        "skill_level": "Local student rides",
    },
    {
        "owner": 8,
        "title": "Photography Session",
        "description": "Graduation, LinkedIn, and event portraits on campus.",
        "category": "Photography",
        "location": "Campus green",
        "allow_other_campuses": True,
        "tags": ["photos", "portrait", "graduation"],
        "image_key": "photography",
        "service_category": ServiceCategory.PHOTOGRAPHY,
        "price_per_hour": 35.0,
        "min_hours": 1,
        "max_hours": 4,
        "skill_level": "Portrait and event photography",
    },
    {
        "owner": 9,
        "title": "Graduation Photoshoot",
        "description": "Quick portrait session for graduation and profile photos.",
        "category": "Photography",
        "location": "Campus lawn",
        "allow_other_campuses": True,
        "tags": ["graduation", "photos", "portrait"],
        "image_key": "photography",
        "service_category": ServiceCategory.PHOTOGRAPHY,
        "price_per_hour": 30.0,
        "min_hours": 1,
        "max_hours": 2,
        "skill_level": "Graduation photo sessions",
    },
    {
        "owner": 0,
        "title": "Resume Review",
        "description": "Helpful feedback for internships, co-ops, and full-time roles.",
        "category": "Writing",
        "location": "Virtual or library",
        "allow_other_campuses": True,
        "tags": ["resume", "career", "review"],
        "image_key": "resume",
        "service_category": ServiceCategory.WRITING,
        "price_per_hour": 16.0,
        "min_hours": 1,
        "max_hours": 2,
        "skill_level": "Career prep",
    },
    {
        "owner": 1,
        "title": "LinkedIn & Resume Help",
        "description": "Feedback on your resume and LinkedIn profile for job applications.",
        "category": "Writing",
        "location": "Virtual",
        "allow_other_campuses": True,
        "tags": ["linkedin", "resume", "career"],
        "image_key": "resume",
        "service_category": ServiceCategory.WRITING,
        "price_per_hour": 18.0,
        "min_hours": 1,
        "max_hours": 2,
        "skill_level": "Internship and job prep",
    },
    {
        "owner": 2,
        "title": "Frontend Coding Help",
        "description": "Help building or polishing React portfolio websites.",
        "category": "Coding",
        "location": "Virtual",
        "allow_other_campuses": True,
        "tags": ["react", "portfolio", "frontend"],
        "image_key": "coding",
        "service_category": ServiceCategory.CODING,
        "price_per_hour": 28.0,
        "min_hours": 1,
        "max_hours": 3,
        "skill_level": "React and frontend development",
    },
    {
        "owner": 3,
        "title": "React Tutoring",
        "description": "Beginner-friendly React guidance for class or portfolio projects.",
        "category": "Coding",
        "location": "Virtual or library",
        "allow_other_campuses": True,
        "tags": ["react", "coding", "tutoring"],
        "image_key": "coding",
        "service_category": ServiceCategory.CODING,
        "price_per_hour": 24.0,
        "min_hours": 1,
        "max_hours": 2,
        "skill_level": "Frontend tutoring",
    },
    {
        "owner": 4,
        "title": "Guitar Lessons",
        "description": "Simple weekly sessions for chords, rhythm, and songs.",
        "category": "Music",
        "location": "Student union",
        "allow_other_campuses": False,
        "tags": ["guitar", "music", "lessons"],
        "image_key": "guitar",
        "service_category": ServiceCategory.MUSIC,
        "price_per_hour": 20.0,
        "min_hours": 1,
        "max_hours": 2,
        "skill_level": "Beginner-friendly instruction",
    },
    {
        "owner": 5,
        "title": "Beginner Guitar Coaching",
        "description": "Relaxed guitar help for absolute beginners learning basics.",
        "category": "Music",
        "location": "Campus lounge",
        "allow_other_campuses": False,
        "tags": ["guitar", "beginner", "music"],
        "image_key": "guitar",
        "service_category": ServiceCategory.MUSIC,
        "price_per_hour": 18.0,
        "min_hours": 1,
        "max_hours": 2,
        "skill_level": "Basic chords and rhythm",
    },
]


async def clear_existing_data(session):
    await session.execute(delete(Rental))
    await session.execute(delete(ServiceBooking))
    await session.execute(delete(ListingImage))
    await session.execute(delete(RentalDetails))
    await session.execute(delete(SaleDetails))
    await session.execute(delete(ServiceDetails))
    await session.execute(delete(Listing))
    await session.execute(delete(User))
    await session.commit()


async def seed_users(session):
    users = []

    for user_data in DEMO_USERS:
        user = User(
            email=user_data["email"],
            password_hash=hash_password(PASSWORD),
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            university=UNIVERSITY,
            bio=f"Demo account for {user_data['first_name']} {user_data['last_name']}.",
            is_email_verified=True,
            is_active=True,
            is_banned=False,
        )
        session.add(user)
        await session.flush()
        users.append(user)

    return users


async def add_listing_image(session, listing_id: str, image_key: str):
    session.add(
        ListingImage(
            listing_id=listing_id,
            url=IMAGE_MAP[image_key],
            public_id=f"seed/{image_key}/{listing_id}",  # REQUIRED FIX
            is_primary=True,
            order=0,
        )
    )


async def seed_listings(session, users):
    created = {
        "rentals": [],
        "sales": [],
        "services": [],
    }

    for item in RENTAL_LISTINGS:
        listing = Listing(
            user_id=users[item["owner"]].id,
            type=ListingType.RENTAL,
            status=ListingStatus.ACTIVE,
            title=item["title"],
            description=item["description"],
            category=item["category"],
            tags=item["tags"],
            university=UNIVERSITY,
            allow_other_campuses=item["allow_other_campuses"],
            location=item["location"],
        )
        session.add(listing)
        await session.flush()

        await add_listing_image(session, listing.id, item["image_key"])

        rd = RentalDetails(
            listing_id=listing.id,
            price_per_period=item["price_per_period"],
            price_period=item["price_period"],
            deposit_amount=item["deposit_amount"],
            min_rental_days=item["min_rental_days"],
        )
        session.add(rd)
        await session.flush()

        created["rentals"].append((listing, rd))

    for item in SALE_LISTINGS:
        listing = Listing(
            user_id=users[item["owner"]].id,
            type=ListingType.SALE,
            status=ListingStatus.ACTIVE,
            title=item["title"],
            description=item["description"],
            category=item["category"],
            tags=item["tags"],
            university=UNIVERSITY,
            allow_other_campuses=item["allow_other_campuses"],
            location=item["location"],
        )
        session.add(listing)
        await session.flush()

        await add_listing_image(session, listing.id, item["image_key"])

        sd = SaleDetails(
            listing_id=listing.id,
            price=item["price"],
            condition=item["condition"],
            is_negotiable=item["is_negotiable"],
            quantity=item["quantity"],
        )
        session.add(sd)
        await session.flush()

        created["sales"].append((listing, sd))

    for item in SERVICE_LISTINGS:
        listing = Listing(
            user_id=users[item["owner"]].id,
            type=ListingType.SERVICE,
            status=ListingStatus.ACTIVE,
            title=item["title"],
            description=item["description"],
            category=item["category"],
            tags=item["tags"],
            university=UNIVERSITY,
            allow_other_campuses=item["allow_other_campuses"],
            location=item["location"],
        )
        session.add(listing)
        await session.flush()

        await add_listing_image(session, listing.id, item["image_key"])

        svd = ServiceDetails(
            listing_id=listing.id,
            category=item["service_category"],
            price_per_hour=item["price_per_hour"],
            min_hours=item["min_hours"],
            max_hours=item["max_hours"],
            skill_level=item["skill_level"],
            availability={
                "monday": ["10:00-12:00", "15:00-18:00"],
                "wednesday": ["13:00-17:00"],
                "friday": ["10:00-14:00"],
            },
        )
        session.add(svd)
        await session.flush()

        created["services"].append((listing, svd))

    return created


async def seed_transactions(session, users, created):
    now = datetime.utcnow()

    rental_pairs = created["rentals"]
    rental_records = [
        Rental(
            listing_id=rental_pairs[0][0].id,
            rental_details_id=rental_pairs[0][1].id,
            renter_id=users[6].id,
            owner_id=users[0].id,
            start_date=now + timedelta(days=2),
            end_date=now + timedelta(days=5),
            total_price=36.0,
            deposit_amount=40.0,
            notes="Need it for campus commuting this week.",
            status=RentalStatus.PENDING,
        ),
        Rental(
            listing_id=rental_pairs[1][0].id,
            rental_details_id=rental_pairs[1][1].id,
            renter_id=users[7].id,
            owner_id=users[1].id,
            start_date=now + timedelta(days=1),
            end_date=now + timedelta(days=3),
            total_price=30.0,
            deposit_amount=50.0,
            notes="Weekend ride around campus.",
            status=RentalStatus.APPROVED,
        ),
        Rental(
            listing_id=rental_pairs[3][0].id,
            rental_details_id=rental_pairs[3][1].id,
            renter_id=users[8].id,
            owner_id=users[3].id,
            start_date=now + timedelta(days=1),
            end_date=now + timedelta(days=2),
            total_price=5.0,
            deposit_amount=15.0,
            notes="Need it for quiz prep.",
            status=RentalStatus.APPROVED,
        ),
        Rental(
            listing_id=rental_pairs[5][0].id,
            rental_details_id=rental_pairs[5][1].id,
            renter_id=users[9].id,
            owner_id=users[5].id,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=1),
            total_price=44.0,
            deposit_amount=80.0,
            notes="Using it for a club media project.",
            status=RentalStatus.ACTIVE,
        ),
        Rental(
            listing_id=rental_pairs[7][0].id,
            rental_details_id=rental_pairs[7][1].id,
            renter_id=users[2].id,
            owner_id=users[7].id,
            start_date=now - timedelta(days=7),
            end_date=now - timedelta(days=5),
            total_price=36.0,
            deposit_amount=50.0,
            notes="Movie night setup for dorm event.",
            status=RentalStatus.RETURNED,
            deposit_returned=True,
            return_notes="Returned in good condition.",
        ),
        Rental(
            listing_id=rental_pairs[9][0].id,
            rental_details_id=rental_pairs[9][1].id,
            renter_id=users[4].id,
            owner_id=users[9].id,
            start_date=now + timedelta(days=7),
            end_date=now + timedelta(days=14),
            total_price=25.0,
            deposit_amount=60.0,
            notes="Need it during move-in week.",
            status=RentalStatus.PENDING,
        ),
        Rental(
            listing_id=rental_pairs[10][0].id,
            rental_details_id=rental_pairs[10][1].id,
            renter_id=users[5].id,
            owner_id=users[0].id,
            start_date=now + timedelta(days=3),
            end_date=now + timedelta(days=10),
            total_price=10.0,
            deposit_amount=20.0,
            notes="Need a desk for a temporary setup.",
            status=RentalStatus.APPROVED,
        ),
        Rental(
            listing_id=rental_pairs[11][0].id,
            rental_details_id=rental_pairs[11][1].id,
            renter_id=users[6].id,
            owner_id=users[1].id,
            start_date=now - timedelta(days=10),
            end_date=now - timedelta(days=3),
            total_price=12.0,
            deposit_amount=25.0,
            notes="Worked great for finals week.",
            status=RentalStatus.RETURNED,
            deposit_returned=True,
            return_notes="No issues on return.",
        ),
    ]
    session.add_all(rental_records)

    service_pairs = created["services"]
    bookings = [
        ServiceBooking(
            listing_id=service_pairs[0][0].id,
            service_details_id=service_pairs[0][1].id,
            client_id=users[0].id,
            provider_id=users[4].id,
            scheduled_at=now + timedelta(days=1, hours=3),
            duration_hours=2,
            total_amount=36.0,
            notes="Need help before the midterm.",
            status=BookingStatus.PENDING,
        ),
        ServiceBooking(
            listing_id=service_pairs[1][0].id,
            service_details_id=service_pairs[1][1].id,
            client_id=users[1].id,
            provider_id=users[5].id,
            scheduled_at=now + timedelta(days=2, hours=2),
            duration_hours=1,
            total_amount=20.0,
            notes="Review session before exam.",
            status=BookingStatus.CONFIRMED,
        ),
        ServiceBooking(
            listing_id=service_pairs[2][0].id,
            service_details_id=service_pairs[2][1].id,
            client_id=users[2].id,
            provider_id=users[6].id,
            scheduled_at=now + timedelta(days=3),
            duration_hours=1,
            total_amount=22.0,
            notes="Ride to CVG with luggage.",
            status=BookingStatus.PENDING,
        ),
        ServiceBooking(
            listing_id=service_pairs[4][0].id,
            service_details_id=service_pairs[4][1].id,
            client_id=users[5].id,
            provider_id=users[8].id,
            scheduled_at=now + timedelta(days=4, hours=2),
            duration_hours=1,
            total_amount=35.0,
            notes="Graduation portrait session.",
            status=BookingStatus.CONFIRMED,
        ),
        ServiceBooking(
            listing_id=service_pairs[6][0].id,
            service_details_id=service_pairs[6][1].id,
            client_id=users[7].id,
            provider_id=users[0].id,
            scheduled_at=now + timedelta(days=1),
            duration_hours=1,
            total_amount=16.0,
            notes="Resume review for internship applications.",
            status=BookingStatus.PENDING,
        ),
        ServiceBooking(
            listing_id=service_pairs[8][0].id,
            service_details_id=service_pairs[8][1].id,
            client_id=users[3].id,
            provider_id=users[2].id,
            scheduled_at=now - timedelta(days=3),
            duration_hours=2,
            total_amount=56.0,
            notes="Portfolio cleanup and deployment.",
            status=BookingStatus.COMPLETED,
        ),
        ServiceBooking(
            listing_id=service_pairs[9][0].id,
            service_details_id=service_pairs[9][1].id,
            client_id=users[4].id,
            provider_id=users[3].id,
            scheduled_at=now + timedelta(days=5),
            duration_hours=2,
            total_amount=48.0,
            notes="Need help understanding components and hooks.",
            status=BookingStatus.CONFIRMED,
        ),
        ServiceBooking(
            listing_id=service_pairs[10][0].id,
            service_details_id=service_pairs[10][1].id,
            client_id=users[8].id,
            provider_id=users[4].id,
            scheduled_at=now + timedelta(days=6),
            duration_hours=1,
            total_amount=20.0,
            notes="Beginner lesson for basic chords.",
            status=BookingStatus.PENDING,
        ),
    ]
    session.add_all(bookings)


async def main():
    async with AsyncSessionLocal() as session:
        await clear_existing_data(session)
        users = await seed_users(session)
        created = await seed_listings(session, users)
        await seed_transactions(session, users, created)

        await session.commit()

        print("Seed complete.")
        print(f"Users: {len(DEMO_USERS)}")
        print(f"Rental listings: {len(RENTAL_LISTINGS)}")
        print(f"Sale listings: {len(SALE_LISTINGS)}")
        print(f"Service listings: {len(SERVICE_LISTINGS)}")
        print("Rental records: 8")
        print("Service bookings: 8")
        print(f"Demo password for all accounts: {PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())