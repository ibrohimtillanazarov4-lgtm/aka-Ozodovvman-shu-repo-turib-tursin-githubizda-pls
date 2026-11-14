import random

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
from keyboards import BTN_QUIZ, CIRCLED, LETTERS, options_kb, quiz_list_kb, result_kb
from states import QuizTaking
from ui import DOT, LINE, THIN, esc, header, percent, progress_bar

router = Router()


async def show_quiz_list(target: Message, user_id: int):
    quizzes = await db.list_quizzes(user_id)
    if not quizzes:
        await target.answer(
            header("📝", "Quizlar") + "\n<blockquote>📭 Hozircha quizlar yo'q.\nYangilari qo'shilganda e'lon qilamiz!</blockquote>"
        )
        return
    await target.answer(
        header("📝", "Quizlar")
        + "\n✅ <i>yechilgan</i>   🔹 <i>yangi</i>\n"
        "<blockquote>Qayta yechsangiz, eng yaxshi natijangiz hisoblanadi.</blockquote>\n"
        "Tanlang 👇",
        reply_markup=quiz_list_kb(quizzes),
    )


@router.message(Command("quizlar"))
@router.message(F.text == BTN_QUIZ)
async def list_quizzes(message: Message, state: FSMContext):
    await state.clear()
    await show_quiz_list(message, message.from_user.id)


@router.callback_query(F.data == "go:quiz")
async def list_quizzes_cb(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await show_quiz_list(call.message, call.from_user.id)


def question_card(title, questions, idx):
    q = questions[idx]
    total = len(questions)
    options = "\n".join(f"{CIRCLED[i]}  {esc(o)}" for i, o in enumerate(q["options"]))
    return (
        f"📝 <b>{esc(title)}</b>\n"
        f"{progress_bar(idx, total)}  <b>{idx + 1}</b>/{total}\n{LINE}\n\n"
        f"<b>{esc(q['text'])}</b>\n\n{options}"
    )


@router.callback_query(F.data.startswith("quiz:"))
async def start_quiz(call: CallbackQuery, state: FSMContext):
    quiz_id = int(call.data.split(":")[1])
    quiz = await db.get_quiz(quiz_id)
    questions = await db.get_questions(quiz_id) if quiz else []
    if not questions:
        await call.answer("Bu quiz topilmadi yoki savollari yo'q", show_alert=True)
        return

    user = call.from_user
    await db.upsert_user(user.id, user.full_name, user.username)

    random.shuffle(questions)  # har safar savollar tartibi boshqacha
    await state.set_state(QuizTaking.active)
    await state.update_data(
        quiz_id=quiz_id, title=quiz["title"], questions=questions, idx=0, score=0
    )
    await call.answer("Omad! 🍀")
    await call.message.answer(
        question_card(quiz["title"], questions, 0),
        reply_markup=options_kb(0, len(questions[0]["options"])),
    )


@router.callback_query(QuizTaking.active, F.data == "quiz_stop")
async def stop_quiz(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("⏹ <b>Quiz to'xtatildi.</b>\n<i>Natija saqlanmadi.</i>")
    await call.answer()


@router.callback_query(QuizTaking.active, F.data.startswith("ans:"))
async def answer(call: CallbackQuery, state: FSMContext):
    _, pos, opt = call.data.split(":")
    pos, opt = int(pos), int(opt)

    data = await state.get_data()
    # eski tugmalar qayta bosilsa e'tiborsiz qoldiramiz
    if pos != data["idx"]:
        await call.answer()
        return

    questions = data["questions"]
    q = questions[pos]
    if opt >= len(q["options"]):
        await call.answer()
        return

    is_correct = opt == q["correct"]
    score = data["score"] + (1 if is_correct else 0)
    # holatni darhol yangilaymiz: ikki marta bosilsa, ikkinchisi e'tiborsiz qoladi
    await state.update_data(idx=pos + 1, score=score)

    right = q["correct"]
    if is_correct:
        verdict = "✅ <b>To'g'ri!</b>"
    else:
        verdict = f"❌ <b>Noto'g'ri</b>\n{DOT} To'g'ri javob: <b>{CIRCLED[right]} {esc(q['options'][right])}</b>"
    await call.message.edit_text(
        f"<b>{esc(q['text'])}</b>\n{THIN}\n"
        f"Sizning javobingiz:  {CIRCLED[opt]} {esc(q['options'][opt])}\n\n{verdict}"
    )
    await call.answer("✅" if is_correct else "❌")

    nxt = pos + 1
    if nxt < len(questions):
        await call.message.answer(
            question_card(data["title"], questions, nxt),
            reply_markup=options_kb(nxt, len(questions[nxt]["options"])),
        )
        return

    await finish_quiz(call, state, data, score, len(questions))


def grade_text(pct):
    if pct >= 90:
        return "🏆 Ajoyib natija!"
    if pct >= 70:
        return "🔥 Juda yaxshi!"
    if pct >= 50:
        return "👍 Yaxshi, yana urinib ko'ring!"
    return "📚 Ko'proq mashq qiling — siz uddalaysiz!"


async def finish_quiz(call: CallbackQuery, state: FSMContext, data, score, total):
    await db.save_result(data["quiz_id"], call.from_user.id, score, total)
    place = await db.quiz_place(data["quiz_id"], call.from_user.id)
    await state.clear()

    pct = percent(score, total)
    text = (
        header("🏁", "Quiz yakunlandi!")
        + f"\n📝 <b>{esc(data['title'])}</b>\n\n"
        f"🎯 Natija:  <b>{score}/{total}</b>  ·  <b>{pct}%</b>\n"
        f"{progress_bar(score, total)}\n\n"
        f"<blockquote>{grade_text(pct)}</blockquote>"
    )
    if place:
        text += f"\n\n{THIN}\n📊 Bu quizdagi o'rningiz:  <b>{place['place']}</b> / {place['n']}"
    await call.message.answer(text, reply_markup=result_kb(data["quiz_id"]))


@router.callback_query(F.data.startswith("ans:"))
async def stale_answer(call: CallbackQuery):
    await call.answer("Bu quiz allaqachon tugagan. Qaytadan boshlang 🙂", show_alert=True)
