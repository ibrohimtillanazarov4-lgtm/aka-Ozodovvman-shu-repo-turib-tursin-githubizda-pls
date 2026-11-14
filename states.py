from aiogram.fsm.state import State, StatesGroup


class NewQuiz(StatesGroup):
    title = State()
    questions = State()


class Broadcast(StatesGroup):
    text = State()
    confirm = State()


class AdminEdit(StatesGroup):
    add_admin = State()
    remove_admin = State()


class AdminReply(StatesGroup):
    text = State()


class QuizTaking(StatesGroup):
    active = State()


class AiChat(StatesGroup):
    active = State()


class Contact(StatesGroup):
    message = State()
