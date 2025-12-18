import os
import django
from django.core.management.base import BaseCommand
from django.conf import settings
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from core.models import Player, Tournament, Registration
from bot.models import LoginToken
from asgiref.sync import sync_to_async
from django.utils import timezone

class Command(BaseCommand):
    help = 'Runs the Telegram bot'

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN
        if not token or token == 'YOUR_BOT_TOKEN_HERE':
            self.stdout.write(self.style.ERROR('TELEGRAM_BOT_TOKEN is not set in settings.py'))
            return

        application = Application.builder().token(token).build()

        # Commands
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("login", self.login))
        application.add_handler(CommandHandler("tournaments", self.tournaments))

        # Message handlers for keyboard buttons
        application.add_handler(MessageHandler(filters.Regex('^🎰 Турниры$'), self.tournaments))
        application.add_handler(MessageHandler(filters.Regex('^🔐 Логин$'), self.login))

        # Callbacks
        application.add_handler(CallbackQueryHandler(self.button_handler))

        self.stdout.write(self.style.SUCCESS('Starting bot polling...'))
        application.run_polling()

    def get_main_keyboard(self):
        """Returns the main menu keyboard"""
        keyboard = [
            [KeyboardButton("🎰 Турниры"), KeyboardButton("🔐 Логин")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        telegram_id = str(user.id)

        # Get or create player
        player, created = await sync_to_async(Player.objects.get_or_create)(
            telegram_id=telegram_id,
            defaults={
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        )

        main_keyboard = self.get_main_keyboard()

        if created:
            await update.message.reply_text(
                f"Добро пожаловать, {user.first_name}! Вы зарегистрированы в Poker System.\n\n"
                f"Используйте меню ниже для навигации:",
                reply_markup=main_keyboard
            )
        else:
            await update.message.reply_text(
                f"С возвращением, {user.first_name}!\n\n"
                f"Используйте меню ниже для навигации:",
                reply_markup=main_keyboard
            )

    async def login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        telegram_id = str(user.id)

        try:
            player = await sync_to_async(Player.objects.get)(telegram_id=telegram_id)

            # Create login token
            token = await sync_to_async(LoginToken.objects.create)(player=player)

            # Generate link using configured site URL
            link = f"{settings.SITE_URL}/bot/login/{token.token}/"

            await update.message.reply_text(
                f"🔐 *Ссылка для входа на сайт:*\n\n"
                f"{link}\n\n"
                f"⚠️ Ссылка одноразовая и действительна только для одного входа.",
                parse_mode='Markdown'
            )
        except Player.DoesNotExist:
            await update.message.reply_text(
                "❌ Вы не зарегистрированы. Пожалуйста, используйте /start сначала."
            )

    async def tournaments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Fetch upcoming tournaments
        user = update.effective_user
        telegram_id = str(user.id)

        now = timezone.now()
        tournaments = await sync_to_async(list)(
            Tournament.objects.filter(status__in=['SCHEDULED', 'RUNNING']).order_by('date')[:5]
        )

        if not tournaments:
            await update.message.reply_text(
                "🎰 На данный момент нет запланированных турниров.\n\n"
                "Проверьте позже!"
            )
            return

        await update.message.reply_text("🎰 *Доступные турниры:*\n", parse_mode='Markdown')

        try:
            player = await sync_to_async(Player.objects.get)(telegram_id=telegram_id)
        except Player.DoesNotExist:
            player = None

        for tournament in tournaments:
            # Check if player is registered for this tournament
            is_registered = False
            if player:
                is_registered = await sync_to_async(
                    Registration.objects.filter(player=player, tournament=tournament).exists
                )()

            # Build keyboard based on registration status
            keyboard = []
            if is_registered:
                tournament_link = f"{settings.SITE_URL}/tournament/{tournament.id}/info/"
                keyboard.append([InlineKeyboardButton("📊 Открыть турнир", url=tournament_link)])
            else:
                keyboard.append([InlineKeyboardButton("✅ Зарегистрироваться", callback_data=f"register_{tournament.id}")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            status_emoji = "🟢" if tournament.status == 'RUNNING' else "📅"
            status_text = "Идёт" if tournament.status == 'RUNNING' else "Запланирован"

            tournament_type = "💰 Платный" if tournament.type == 'PAID' else "🆓 Бесплатный"

            registration_status = "\n✅ *Вы зарегистрированы*" if is_registered else ""

            await update.message.reply_text(
                f"{status_emoji} *{tournament.name}*\n\n"
                f"📅 Дата: {tournament.date.strftime('%d.%m.%Y %H:%M')}\n"
                f"📊 Статус: {status_text}\n"
                f"💵 Тип: {tournament_type}\n"
                f"💸 Бай-ин: ${tournament.buy_in if tournament.buy_in else 'Бесплатно'}"
                f"{registration_status}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        data = query.data
        user = update.effective_user
        telegram_id = str(user.id)

        if data.startswith("register_"):
            tournament_id = int(data.split("_")[1])

            try:
                player = await sync_to_async(Player.objects.get)(telegram_id=telegram_id)
                tournament = await sync_to_async(Tournament.objects.get)(id=tournament_id)

                # Check if already registered
                exists = await sync_to_async(Registration.objects.filter(player=player, tournament=tournament).exists)()

                if exists:
                    tournament_link = f"{settings.SITE_URL}/tournament/{tournament.id}/info/"
                    keyboard = [[InlineKeyboardButton("📊 Открыть турнир", url=tournament_link)]]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await query.edit_message_reply_markup(reply_markup=reply_markup)
                    await query.message.reply_text(
                        f"ℹ️ Вы уже зарегистрированы на турнир *{tournament.name}*",
                        parse_mode='Markdown'
                    )
                else:
                    await sync_to_async(Registration.objects.create)(
                        player=player,
                        tournament=tournament,
                        status='REGISTERED'
                    )

                    tournament_link = f"{settings.SITE_URL}/tournament/{tournament.id}/info/"
                    keyboard = [[InlineKeyboardButton("📊 Открыть турнир", url=tournament_link)]]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await query.edit_message_reply_markup(reply_markup=reply_markup)
                    await query.message.reply_text(
                        f"✅ Вы успешно зарегистрированы на турнир *{tournament.name}*!\n\n"
                        f"Увидимся за столами! 🎰",
                        parse_mode='Markdown'
                    )

            except Player.DoesNotExist:
                await query.message.reply_text(
                    "❌ Вы не зарегистрированы. Пожалуйста, используйте /start сначала."
                )
            except Tournament.DoesNotExist:
                await query.message.reply_text("❌ Турнир не найден.")
