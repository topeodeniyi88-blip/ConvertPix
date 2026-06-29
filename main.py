import os
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

from utils.converter import ImageConverter

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Create temp directories
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# Supported formats
SUPPORTED_FORMATS = ["PNG", "JPG", "JPEG", "WEBP", "BMP", "ICO", "GIF", "TIFF"]

# States for conversation
class ConversionStates(StatesGroup):
    waiting_for_image = State()
    selecting_target_format = State()
    confirming_conversion = State()

# ============ KEYBOARDS ============

def get_format_keyboard(source_format: Optional[str] = None) -> InlineKeyboardMarkup:
    """Generate keyboard with format selection"""
    keyboard = []
    row = []
    
    for i, fmt in enumerate(SUPPORTED_FORMATS):
        # Skip the source format if provided
        if source_format and fmt == source_format:
            continue
        
        # Add callback data with source format if provided
        if source_format:
            callback_data = f"convert_{source_format}_{fmt}"
        else:
            callback_data = f"format_{fmt}"
        
        row.append(InlineKeyboardButton(text=fmt, callback_data=callback_data))
        
        # Create new row after every 3 buttons
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    # Add cancel button
    keyboard.append([InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ============ COMMAND HANDLERS ============

@dp.message(Command("start"))
async def start_command(message: Message):
    """Handle /start command"""
    welcome_text = (
        f"👋 Hello {message.from_user.first_name}!\n\n"
        "I'm **ConvertPix Bot** - your image conversion assistant!\n\n"
        "📸 **What I can do:**\n"
        "• Convert images between PNG, JPG, WEBP, BMP, ICO, GIF, TIFF\n"
        "• Batch image processing\n"
        "• High-quality conversions\n\n"
        "🔧 **How to use:**\n"
        "1️⃣ Send /convert to start conversion\n"
        "2️⃣ Choose your target format\n"
        "3️⃣ Upload the image you want to convert\n"
        "4️⃣ Download your converted image!\n\n"
        "📊 **Commands:**\n"
        "/start - Show this menu\n"
        "/convert - Start image conversion\n"
        "/formats - List supported formats\n"
        "/about - About this bot\n"
        "/help - Get help"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Convert Now", callback_data="start_convert"),
                InlineKeyboardButton(text="📋 Formats", callback_data="show_formats")
            ],
            [
                InlineKeyboardButton(text="ℹ️ About", callback_data="show_about")
            ]
        ]
    )
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Command("convert"))
async def convert_command(message: Message, state: FSMContext):
    """Handle /convert command"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Upload Image", callback_data="upload_image")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
        ]
    )
    
    await message.answer(
        "🔄 **Image Conversion Started!**\n\n"
        "Please select an option below:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(ConversionStates.waiting_for_image)

@dp.message(Command("formats"))
async def formats_command(message: Message):
    """Handle /formats command"""
    formats_text = "📋 **Supported Image Formats:**\n\n" + "\n".join([f"• {fmt}" for fmt in SUPPORTED_FORMATS])
    await message.answer(formats_text, parse_mode="Markdown")

@dp.message(Command("about"))
async def about_command(message: Message):
    """Handle /about command"""
    about_text = (
        "🤖 **ConvertPix Bot**\n\n"
        "Version: 1.0.0\n"
        "Created with ❤️ using Aiogram\n\n"
        "🔹 **Features:**\n"
        "• Convert between 8 image formats\n"
        "• High-quality output\n"
        "• Fast processing\n"
        "• User-friendly interface\n\n"
        "📌 **Developed for:** @ConvertPix_Bot"
    )
    await message.answer(about_text, parse_mode="Markdown")

@dp.message(Command("help"))
async def help_command(message: Message):
    """Handle /help command"""
    help_text = (
        "🆘 **Help & Support**\n\n"
        "📖 **Basic Usage:**\n"
        "1. Send /convert to start\n"
        "2. Choose target format\n"
        "3. Upload image\n"
        "4. Wait for conversion\n\n"
        "⚡ **Tips:**\n"
        "• You can convert multiple images one by one\n"
        "• Cancel any operation with the ❌ button\n"
        "• Large images may take a few seconds\n\n"
        "❓ **Need more help?**\n"
        "Contact support or check our documentation."
    )
    await message.answer(help_text, parse_mode="Markdown")

# ============ CALLBACK QUERY HANDLERS ============

@dp.callback_query(lambda c: c.data == "start_convert")
async def start_convert_callback(callback: CallbackQuery, state: FSMContext):
    """Handle start conversion from callback"""
    await callback.answer()
    await convert_command(callback.message, state)
    await callback.message.delete()

@dp.callback_query(lambda c: c.data == "show_formats")
async def show_formats_callback(callback: CallbackQuery):
    """Handle show formats from callback"""
    await callback.answer()
    formats_text = "📋 **Supported Image Formats:**\n\n" + "\n".join([f"• {fmt}" for fmt in SUPPORTED_FORMATS])
    await callback.message.answer(formats_text, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "show_about")
async def show_about_callback(callback: CallbackQuery):
    """Handle show about from callback"""
    await callback.answer()
    await about_command(callback.message)

@dp.callback_query(lambda c: c.data == "upload_image")
async def upload_image_callback(callback: CallbackQuery, state: FSMContext):
    """Handle upload image callback"""
    await callback.answer()
    
    # Ask for format selection first
    keyboard = get_format_keyboard()
    await callback.message.answer(
        "📐 **Select Target Format:**\n\nChoose the format you want to convert to:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(ConversionStates.selecting_target_format)

@dp.callback_query(lambda c: c.data.startswith("format_"))
async def format_selection_callback(callback: CallbackQuery, state: FSMContext):
    """Handle format selection from callback"""
    await callback.answer()
    
    # Extract selected format
    target_format = callback.data.split("_")[1]
    
    # Store format in state
    await state.update_data(target_format=target_format)
    
    await callback.message.answer(
        f"✅ Selected format: **{target_format}**\n\n"
        "📤 **Now send me the image you want to convert.**\n"
        "You can send it as a photo or file.",
        parse_mode="Markdown"
    )
    await state.set_state(ConversionStates.waiting_for_image)

@dp.callback_query(lambda c: c.data.startswith("convert_"))
async def convert_callback(callback: CallbackQuery, state: FSMContext):
    """Handle conversion callback with source and target formats"""
    await callback.answer()
    
    # Extract formats
    _, source_format, target_format = callback.data.split("_")
    
    # Store formats
    await state.update_data(source_format=source_format, target_format=target_format)
    
    await callback.message.answer(
        f"🔄 Converting **{source_format}** → **{target_format}**\n\n"
        "📤 **Please upload your image:**",
        parse_mode="Markdown"
    )
    await state.set_state(ConversionStates.waiting_for_image)

@dp.callback_query(lambda c: c.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    """Handle cancel callback"""
    await callback.answer()
    await state.clear()
    await callback.message.answer(
        "❌ Operation cancelled. Use /convert to start again.",
        parse_mode="Markdown"
    )

# ============ MESSAGE HANDLERS ============

@dp.message(ConversionStates.waiting_for_image)
async def handle_image(message: Message, state: FSMContext):
    """Handle image upload for conversion"""
    try:
        # Check if message has photo or document
        if not message.photo and not message.document:
            await message.answer(
                "⚠️ Please send an image file.\n"
                "You can send it as a photo or document."
            )
            return
        
        # Get file from message
        if message.photo:
            file = message.photo[-1]  # Get highest quality
            file_extension = "jpg"  # Telegram photos are JPG
            file_name = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        else:
            file = message.document
            file_extension = file.file_name.split('.')[-1].lower() if file.file_name else "jpg"
            file_name = file.file_name or f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        
        # Send processing message
        processing_msg = await message.answer("⏳ Processing your image...")
        
        # Download file
        file_path = TEMP_DIR / file_name
        await bot.download(file, file_path)
        
        # Get target format from state
        state_data = await state.get_data()
        target_format = state_data.get("target_format", "PNG")
        source_format = state_data.get("source_format", None)
        
        # Convert image
        converter = ImageConverter()
        
        # Detect source format if not provided
        if not source_format:
            source_format = file_extension.upper()
        
        # Perform conversion
        output_format = target_format.lower()
        output_file = TEMP_DIR / f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{output_format}"
        
        success, result = await converter.convert(
            input_path=file_path,
            output_path=output_file,
            target_format=output_format,
            quality=90
        )
        
        if not success:
            await processing_msg.edit_text(f"❌ Conversion failed: {result}")
            return
        
        # Send converted image
        await processing_msg.delete()
        
        # Create caption
        original_size = file_path.stat().st_size / 1024  # KB
        new_size = output_file.stat().st_size / 1024  # KB
        
        caption = (
            f"✅ **Conversion Complete!**\n\n"
            f"📄 **{source_format}** → **{target_format}**\n"
            f"📊 Size: {original_size:.1f}KB → {new_size:.1f}KB\n"
            f"📥 Download your image below:"
        )
        
        # Send as document (supports all formats)
        document = FSInputFile(output_file, filename=output_file.name)
        await message.answer_document(
            document,
            caption=caption,
            parse_mode="Markdown"
        )
        
        # Cleanup temp files
        try:
            file_path.unlink()
            output_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete temp files: {e}")
        
        # Clear state
        await state.clear()
        
        # Ask if user wants to convert more
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Convert Another", callback_data="start_convert")],
                [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
            ]
        )
        
        await message.answer(
            "🎯 **Convert another image?**",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_image: {e}")
        await message.answer(f"❌ An error occurred: {str(e)}")
        await state.clear()

@dp.message()
async def handle_unknown(message: Message):
    """Handle unknown messages"""
    await message.answer(
        "❓ I don't understand that command.\n\n"
        "Use /help to see available commands or /start to get started."
    )

# ============ MAIN ============

async def main():
    """Main entry point"""
    logger.info("🚀 Starting ConvertPix Bot...")
    
    # Set webhook for Railway (if needed)
    # For polling (recommended for Railway):
    await dp.start_polling(bot)
    
    logger.info("✅ Bot is running!")

if __name__ == "__main__":
    asyncio.run(main())
