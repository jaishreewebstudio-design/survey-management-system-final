import os


class Config:

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "survey_management_system_secret_key_2026"
    )

    DATABASE = os.environ.get(
        "DATABASE",
        "survey.db"
    )

    DEBUG = True