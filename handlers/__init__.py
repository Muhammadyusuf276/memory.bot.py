from aiogram import Router

from handlers.start import router as start_router
from handlers.folders import router as folders_router
from handlers.contacts import router as contacts_router
from handlers.notes import router as notes_router
from handlers.links import router as links_router
from handlers.schedule import router as schedule_router
from handlers.files import router as files_router
from handlers.admin import router as admin_router


def setup_routers() -> Router:
    """Barcha router'larni bitta asosiy router'ga birlashtirish."""
    main_router = Router()
    main_router.include_router(start_router)
    main_router.include_router(folders_router)
    main_router.include_router(contacts_router)
    main_router.include_router(notes_router)
    main_router.include_router(links_router)
    main_router.include_router(schedule_router)
    main_router.include_router(files_router)
    main_router.include_router(admin_router)
    return main_router
