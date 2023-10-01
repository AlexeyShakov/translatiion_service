import enum


class StepNameChoice(enum.Enum):
    TRANSTALTION = "translation"
    TELEGRAM = "telegram"
    SENDING_TO_TRANSLATION = "sending_to_translation"
    SENDING_TO_TELEGRAM = "sending_to_telegram"
