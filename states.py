from aiogram.fsm.state import State, StatesGroup


class FolderStates(StatesGroup):
    """Papka yaratish uchun holatlar."""
    creating_folder = State()
    selecting_color = State()
    setting_password = State()
    entering_password = State()
    uploading_file = State()


class ContactStates(StatesGroup):
    """Kontakt qo'shish uchun holatlar."""
    adding_phone = State()
    adding_name = State()
    adding_note = State()


class NoteStates(StatesGroup):
    """Eslatma qo'shish uchun holatlar."""
    adding_title = State()
    adding_content = State()


class LinkStates(StatesGroup):
    """Link qo'shish uchun holatlar."""
    adding_url = State()
    adding_title = State()
    adding_description = State()


class ScheduleStates(StatesGroup):
    """Kun tartibi uchun holatlar."""
    adding_task = State()
    adding_time = State()


class AdminStates(StatesGroup):
    """Admin paneili uchun holatlar."""
    waiting_for_broadcast = State()
