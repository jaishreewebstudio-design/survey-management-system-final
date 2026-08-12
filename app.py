import os
import csv
import io
import json
import sqlite3
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    make_response,
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from config import Config
from flask_swagger_ui import get_swaggerui_blueprint


# ============================================================
# APP
# ============================================================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="vstatic",
)

app.config.from_object(Config)
app.secret_key = app.config["SECRET_KEY"]

DATABASE = app.config["DATABASE"]


# ============================================================
# SWAGGER / OPENAPI
# ============================================================

SWAGGER_URL = "/swagger"
API_URL = "/swagger.json"

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": "Survey Management System API",
        "docExpansion": "list",
        "defaultModelsExpandDepth": 1,
    },
)

app.register_blueprint(
    swaggerui_blueprint,
    url_prefix=SWAGGER_URL,
)


# ============================================================
# OPENAPI DOCUMENTATION
# ============================================================

OPENAPI_SPEC = {
    "openapi": "3.0.3",

    "info": {
        "title": "Survey Management System API",
        "description": (
            "REST API documentation for the "
            "Survey Management System internship project."
        ),
        "version": "2.0.0",
    },

    "servers": [
        {
            "url": "/",
        }
    ],

    "tags": [
        {
            "name": "Authentication",
            "description": "User authentication APIs",
        },
        {
            "name": "Users",
            "description": "User management APIs",
        },
        {
            "name": "Surveys",
            "description": "Survey management APIs",
        },
        {
            "name": "Questions",
            "description": "Survey question APIs",
        },
        {
            "name": "Responses",
            "description": "Survey response APIs",
        },
        {
            "name": "Dashboard",
            "description": "Dashboard statistics APIs",
        },
        {
            "name": "Reports",
            "description": "Survey reports and statistics APIs",
        },
    ],

    "paths": {
        "/api/register": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Register User",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/RegisterRequest"
                            }
                        }
                    },
                },
                "responses": {
                    "201": {"description": "Registration successful"},
                    "400": {"description": "Invalid registration data"},
                    "409": {"description": "Email already registered"},
                },
            }
        },

        "/api/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Login User",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/LoginRequest"
                            }
                        }
                    },
                },
                "responses": {
                    "200": {"description": "Login successful"},
                    "401": {"description": "Invalid email or password"},
                },
            }
        },

        "/api/logout": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Logout User",
                "responses": {
                    "200": {"description": "Logout successful"},
                },
            }
        },

        "/api/forgot-password": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Reset Password",
                "description": "Reset a user's password using the registered email address.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ForgotPasswordRequest"
                            }
                        }
                    },
                },
                "responses": {
                    "200": {"description": "Password reset successful"},
                    "400": {"description": "Invalid password reset data"},
                    "404": {"description": "Email not registered"},
                },
            }
        },

        "/api/me": {
            "get": {
                "tags": ["Authentication"],
                "summary": "Get Current User",
                "responses": {
                    "200": {"description": "Current logged-in user"},
                    "401": {"description": "Authentication required"},
                },
            }
        },

        "/api/users": {
            "get": {
                "tags": ["Users"],
                "summary": "Get Users",
                "responses": {
                    "200": {"description": "List of users"},
                },
            },
            "post": {
                "tags": ["Users"],
                "summary": "Create User",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/UserCreateRequest"
                            }
                        }
                    },
                },
                "responses": {
                    "201": {"description": "User created"},
                    "400": {"description": "Invalid user data"},
                    "409": {"description": "Email already registered"},
                },
            },
        },

        "/api/users/{user_id}": {
            "get": {
                "tags": ["Users"],
                "summary": "Get User",
                "parameters": [
                    {"$ref": "#/components/parameters/UserId"}
                ],
                "responses": {
                    "200": {"description": "User details"},
                    "404": {"description": "User not found"},
                },
            },
            "put": {
                "tags": ["Users"],
                "summary": "Update User",
                "parameters": [
                    {"$ref": "#/components/parameters/UserId"}
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/UserUpdateRequest"
                            }
                        }
                    },
                },
                "responses": {
                    "200": {"description": "User updated"},
                    "403": {"description": "Permission denied"},
                    "404": {"description": "User not found"},
                },
            },
            "delete": {
                "tags": ["Users"],
                "summary": "Delete User",
                "parameters": [
                    {"$ref": "#/components/parameters/UserId"}
                ],
                "responses": {
                    "200": {"description": "User deleted"},
                    "403": {"description": "Permission denied"},
                    "404": {"description": "User not found"},
                },
            },
        },

        "/api/surveys": {
            "get": {
                "tags": ["Surveys"],
                "summary": "Get All Surveys",
                "responses": {
                    "200": {"description": "Survey list"},
                },
            },
            "post": {
                "tags": ["Surveys"],
                "summary": "Create Survey",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/SurveyRequest"
                            }
                        }
                    },
                },
                "responses": {
                    "201": {"description": "Survey created"},
                    "400": {"description": "Invalid survey"},
                },
            },
        },

        "/api/surveys/{survey_id}": {
            "get": {
                "tags": ["Surveys"],
                "summary": "Get Survey",
                "parameters": [
                    {"$ref": "#/components/parameters/SurveyId"}
                ],
                "responses": {
                    "200": {"description": "Survey details"},
                    "404": {"description": "Survey not found"},
                },
            },
            "put": {
                "tags": ["Surveys"],
                "summary": "Update Own Survey Response",
                "description": (
                    "Updates only the response belonging to the currently "
                    "logged-in user. A user cannot edit another user's response."
                ),
                "parameters": [
                    {"$ref": "#/components/parameters/SurveyId"}
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/SurveyRequest"
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Own response updated successfully"
                    },
                    "403": {
                        "description": (
                            "The logged-in user does not have "
                            "their own response for this survey"
                        )
                    },
                },
            },
            "delete": {
                "tags": ["Surveys"],
                "summary": "Delete Survey",
                "parameters": [
                    {"$ref": "#/components/parameters/SurveyId"}
                ],
                "responses": {
                    "200": {"description": "Survey deleted"},
                    "403": {"description": "Permission denied"},
                    "404": {"description": "Survey not found"},
                },
            },
        },

        "/api/surveys/{survey_id}/publish": {
            "post": {
                "tags": ["Surveys"],
                "summary": "Publish Survey",
                "parameters": [
                    {"$ref": "#/components/parameters/SurveyId"}
                ],
                "responses": {
                    "200": {"description": "Survey published"},
                },
            }
        },

        "/api/surveys/{survey_id}/questions": {
            "get": {
                "tags": ["Questions"],
                "summary": "Get Questions",
                "parameters": [
                    {"$ref": "#/components/parameters/SurveyId"}
                ],
                "responses": {
                    "200": {"description": "Survey questions"},
                },
            },
            "post": {
                "tags": ["Questions"],
                "summary": "Add Question",
                "parameters": [
                    {"$ref": "#/components/parameters/SurveyId"}
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/QuestionRequest"
                            }
                        }
                    },
                },
                "responses": {
                    "201": {"description": "Question added"},
                    "400": {"description": "Invalid question"},
                },
            },
        },

        "/api/questions/{question_id}": {
            "put": {
                "tags": ["Questions"],
                "summary": "Update Question",
                "parameters": [
                    {"$ref": "#/components/parameters/QuestionId"}
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/QuestionRequest"
                            }
                        }
                    },
                },
                "responses": {
                    "200": {"description": "Question updated"},
                },
            },
            "delete": {
                "tags": ["Questions"],
                "summary": "Delete Question",
                "parameters": [
                    {"$ref": "#/components/parameters/QuestionId"}
                ],
                "responses": {
                    "200": {"description": "Question deleted"},
                },
            },
        },

        "/api/responses": {
            "get": {
                "tags": ["Responses"],
                "summary": "Get All Responses",
                "responses": {
                    "200": {"description": "Response list"},
                },
            },
            "post": {
                "tags": ["Responses"],
                "summary": "Submit Response",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ResponseRequest"
                            }
                        }
                    },
                },
                "responses": {
                    "201": {"description": "Response submitted"},
                    "400": {"description": "Invalid response"},
                },
            },
        },

        "/api/responses/{response_id}": {
            "get": {
                "tags": ["Responses"],
                "summary": "Get Response",
                "parameters": [
                    {"$ref": "#/components/parameters/ResponseId"}
                ],
                "responses": {
                    "200": {"description": "Response details"},
                },
            },
            "delete": {
                "tags": ["Responses"],
                "summary": "Delete Response",
                "parameters": [
                    {"$ref": "#/components/parameters/ResponseId"}
                ],
                "responses": {
                    "200": {"description": "Response deleted"},
                },
            },
        },

        "/api/surveys/{survey_id}/responses": {
            "get": {
                "tags": ["Responses"],
                "summary": "Get Survey Responses",
                "parameters": [
                    {"$ref": "#/components/parameters/SurveyId"}
                ],
                "responses": {
                    "200": {"description": "Responses belonging to survey"},
                },
            },
        },

        "/api/dashboard": {
            "get": {
                "tags": ["Dashboard"],
                "summary": "Dashboard Statistics",
                "responses": {
                    "200": {"description": "Dashboard statistics"},
                },
            }
        },

        "/api/reports/survey/{survey_id}": {
            "get": {
                "tags": ["Reports"],
                "summary": "Survey Report",
                "parameters": [
                    {"$ref": "#/components/parameters/SurveyId"}
                ],
                "responses": {
                    "200": {"description": "Survey report"},
                },
            }
        },

        "/api/reports/survey/{survey_id}/statistics": {
            "get": {
                "tags": ["Reports"],
                "summary": "Survey Statistics",
                "parameters": [
                    {"$ref": "#/components/parameters/SurveyId"}
                ],
                "responses": {
                    "200": {"description": "Survey statistics"},
                },
            }
        },

        "/api/reports/survey/{survey_id}/export": {
            "get": {
                "tags": ["Reports"],
                "summary": "Export Report as CSV",
                "parameters": [
                    {"$ref": "#/components/parameters/SurveyId"}
                ],
                "responses": {
                    "200": {"description": "CSV report"},
                },
            }
        },
    },

    "components": {
        "parameters": {
            "UserId": {
                "name": "user_id",
                "in": "path",
                "required": True,
                "schema": {"type": "integer"},
            },
            "SurveyId": {
                "name": "survey_id",
                "in": "path",
                "required": True,
                "schema": {"type": "integer"},
            },
            "QuestionId": {
                "name": "question_id",
                "in": "path",
                "required": True,
                "schema": {"type": "integer"},
            },
            "ResponseId": {
                "name": "response_id",
                "in": "path",
                "required": True,
                "schema": {"type": "integer"},
            },
        },

        "schemas": {
            "RegisterRequest": {
                "type": "object",
                "required": [
                    "name",
                    "email",
                    "password",
                    "confirm_password",
                ],
                "properties": {
                    "name": {"type": "string", "example": "Jaishree"},
                    "email": {
                        "type": "string",
                        "format": "email",
                        "example": "jaishree@gmail.com",
                    },
                    "mobile": {
                        "type": "string",
                        "example": "9876543210",
                    },
                    "password": {
                        "type": "string",
                        "example": "123654",
                    },
                    "confirm_password": {
                        "type": "string",
                        "example": "123654",
                    },
                },
            },

            "LoginRequest": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {
                        "type": "string",
                        "format": "email",
                        "example": "jaishree@gmail.com",
                    },
                    "password": {
                        "type": "string",
                        "example": "123654",
                    },
                },
            },

            "ForgotPasswordRequest": {
                "type": "object",
                "required": ["email", "new_password", "confirm_password"],
                "properties": {
                    "email": {
                        "type": "string",
                        "format": "email",
                        "example": "jaishree@gmail.com",
                    },
                    "new_password": {
                        "type": "string",
                        "example": "654321",
                    },
                    "confirm_password": {
                        "type": "string",
                        "example": "654321",
                    },
                },
            },

            "UserCreateRequest": {
                "type": "object",
                "required": ["name", "email", "password"],
                "properties": {
                    "name": {"type": "string", "example": "Jaishree"},
                    "email": {
                        "type": "string",
                        "format": "email",
                        "example": "jaishree@gmail.com",
                    },
                    "mobile": {
                        "type": "string",
                        "example": "9876543210",
                    },
                    "password": {
                        "type": "string",
                        "example": "123654",
                    },
                },
            },

            "UserUpdateRequest": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "example": "Jaishree Updated"},
                    "email": {
                        "type": "string",
                        "format": "email",
                        "example": "new@example.com",
                    },
                    "mobile": {
                        "type": "string",
                        "example": "9876543210",
                    },
                    "password": {
                        "type": "string",
                        "example": "newpassword",
                    },
                },
            },

            "QuestionRequest": {
                "type": "object",
                "required": ["question"],
                "properties": {
                    "question": {
                        "type": "string",
                        "example": "How satisfied are you?",
                    },
                    "question_type": {
                        "type": "string",
                        "example": "multiple_choice",
                    },
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "example": [
                            "Very Satisfied",
                            "Satisfied",
                            "Not Satisfied",
                        ],
                    },
                    "required": {
                        "type": "boolean",
                        "example": True,
                    },
                },
            },

            "SurveyRequest": {
                "type": "object",
                "required": ["title", "questions"],
                "properties": {
                    "title": {
                        "type": "string",
                        "example": "Customer Feedback Survey",
                    },
                    "description": {
                        "type": "string",
                        "example": "Customer satisfaction survey",
                    },
                    "questions": {
                        "type": "array",
                        "minItems": 6,
                        "maxItems": 6,
                        "items": {
                            "$ref": "#/components/schemas/QuestionRequest"
                        },
                    },
                },
            },

            "ResponseRequest": {
                "type": "object",
                "required": ["survey_id", "answers"],
                "properties": {
                    "survey_id": {
                        "type": "integer",
                        "example": 1,
                    },
                    "name": {
                        "type": "string",
                        "example": "Jaishree",
                    },
                    "email": {
                        "type": "string",
                        "format": "email",
                        "example": "jaishree@gmail.com",
                    },
                    "answers": {
                        "type": "object",
                        "example": {
                            "1": "Very Satisfied",
                            "2": "Good",
                        },
                    },
                },
            },
        },
    },
}


# ============================================================
# SWAGGER JSON ROUTE
# ============================================================

@app.get("/swagger.json")
def swagger_json():
    return jsonify(OPENAPI_SPEC)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(
        DATABASE,
        timeout=20,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 20000")
    return conn


def init_db():
    conn = get_db()

    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                mobile TEXT,
                password TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                created_by INTEGER,
                status TEXT DEFAULT 'draft',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                published_at TEXT,
                FOREIGN KEY(created_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS survey_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                question_type TEXT NOT NULL,
                options TEXT DEFAULT '[]',
                required INTEGER DEFAULT 0,
                question_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(survey_id)
                    REFERENCES surveys(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_id INTEGER NOT NULL,
                user_id INTEGER,
                name TEXT,
                email TEXT,
                answers TEXT NOT NULL,
                submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(survey_id)
                    REFERENCES surveys(id)
                    ON DELETE CASCADE,
                FOREIGN KEY(user_id)
                    REFERENCES users(id)
            );
            """
        )

        migrations = {
            "users": {
                "mobile": "TEXT",
                "created_at": "TEXT",
            },
            "surveys": {
                "description": "TEXT",
                "created_by": "INTEGER",
                "status": "TEXT",
                "created_at": "TEXT",
                "published_at": "TEXT",
            },
            "survey_questions": {
                "question": "TEXT",
                "question_type": "TEXT",
                "options": "TEXT",
                "required": "INTEGER",
                "question_order": "INTEGER",
                "created_at": "TEXT",
            },
            "responses": {
                "survey_id": "INTEGER",
                "user_id": "INTEGER",
                "name": "TEXT",
                "email": "TEXT",
                "answers": "TEXT",
                "submitted_at": "TEXT",
            },
        }

        for table, columns in migrations.items():
            existing_columns = {
                row["name"]
                for row in conn.execute(
                    f"PRAGMA table_info({table})"
                ).fetchall()
            }

            for column, column_type in columns.items():
                if column not in existing_columns:
                    conn.execute(
                        f"""
                        ALTER TABLE {table}
                        ADD COLUMN {column} {column_type}
                        """
                    )

        conn.execute(
            """
            UPDATE surveys
            SET status = 'draft'
            WHERE status IS NULL OR status = ''
            """
        )

        conn.execute(
            """
            UPDATE survey_questions
            SET options = '[]'
            WHERE options IS NULL OR options = ''
            """
        )

        conn.execute(
            """
            UPDATE survey_questions
            SET question_order = id
            WHERE question_order IS NULL OR question_order = 0
            """
        )

        conn.execute(
            """
            UPDATE responses
            SET submitted_at = CURRENT_TIMESTAMP
            WHERE submitted_at IS NULL OR submitted_at = ''
            """
        )

        conn.commit()

        print("==========================================")
        print("DATABASE READY")
        print("DATABASE:", DATABASE)
        print("==========================================")

    except Exception as e:
        conn.rollback()
        print("DATABASE ERROR:", e)
        raise

    finally:
        conn.close()


# ============================================================
# AUTH HELPERS
# ============================================================

def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    conn = get_db()

    try:
        return conn.execute(
            """
            SELECT id, name, email, mobile, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
    finally:
        conn.close()


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            session.clear()

            if request.path.startswith("/api/"):
                return jsonify(
                    success=False,
                    message="Please login again.",
                ), 401

            return redirect(url_for("login_page"))

        return function(*args, **kwargs)

    return wrapper


def owner_required(created_by):
    return created_by == session.get("user_id")


# ============================================================
# PAGE ROUTES
# ============================================================

@app.route("/")
def home():
    if current_user():
        return redirect(url_for("dashboard"))

    return redirect(url_for("login_page"))


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/forgot-password")
def forgot_password_page():
    return render_template("forget-pass.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/add-survey")
@login_required
def add_survey():
    return render_template("add-survey.html")


@app.route("/surveys")
@login_required
def surveys():
    return render_template("surveys.html")


@app.route("/edit-survey/<int:survey_id>")
@login_required
def edit_survey_page(survey_id):
    return render_template(
        "edit-survey.html",
        survey_id=survey_id,
    )


@app.route("/view-survey/<int:survey_id>")
@login_required
def view_survey_page(survey_id):
    return render_template(
        "view-survey.html",
        survey_id=survey_id,
    )


@app.route("/responses")
@login_required
def responses():
    return render_template("responses.html")


@app.route("/success")
@login_required
def success():
    return render_template("success.html")


# ============================================================
# AUTH API
# ============================================================

@app.post("/api/register")
def api_register():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    mobile = str(data.get("mobile", "")).strip()
    password = str(data.get("password", ""))
    confirm_password = str(data.get("confirm_password", ""))

    if not name:
        return jsonify(
            success=False,
            message="Name is required.",
        ), 400

    if not email:
        return jsonify(
            success=False,
            message="Email is required.",
        ), 400

    if not password:
        return jsonify(
            success=False,
            message="Password is required.",
        ), 400

    if password != confirm_password:
        return jsonify(
            success=False,
            message="Passwords do not match.",
        ), 400

    if len(password) < 6:
        return jsonify(
            success=False,
            message="Password must be at least 6 characters.",
        ), 400

    conn = get_db()

    try:
        conn.execute(
            """
            INSERT INTO users
            (name, email, mobile, password)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                mobile,
                generate_password_hash(password),
            ),
        )

        conn.commit()

        return jsonify(
            success=True,
            message="Registration successful.",
        ), 201

    except sqlite3.IntegrityError:
        return jsonify(
            success=False,
            message="Email already registered.",
        ), 409

    finally:
        conn.close()


@app.post("/api/login")
def api_login():
    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        return jsonify(
            success=False,
            message="Email and password are required.",
        ), 400

    conn = get_db()

    try:
        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()
    finally:
        conn.close()

    if not user:
        return jsonify(
            success=False,
            message="Invalid email or password.",
        ), 401

    if not check_password_hash(user["password"], password):
        return jsonify(
            success=False,
            message="Invalid email or password.",
        ), 401

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]

    return jsonify(
        success=True,
        message="Login successful.",
        redirect=url_for("dashboard"),
    )


@app.post("/api/forgot-password")
def api_forgot_password():
    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    new_password = str(data.get("new_password", ""))
    confirm_password = str(data.get("confirm_password", ""))

    if not email:
        return jsonify(
            success=False,
            message="Email is required.",
        ), 400

    if not new_password:
        return jsonify(
            success=False,
            message="New password is required.",
        ), 400

    if new_password != confirm_password:
        return jsonify(
            success=False,
            message="Passwords do not match.",
        ), 400

    if len(new_password) < 6:
        return jsonify(
            success=False,
            message="Password must be at least 6 characters.",
        ), 400

    conn = get_db()

    try:
        user = conn.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(TRIM(email)) = ?
            LIMIT 1
            """,
            (email,),
        ).fetchone()

        if not user:
            return jsonify(
                success=False,
                message="No account found with this email address.",
            ), 404

        password_hash = generate_password_hash(new_password)

        conn.execute(
            """
            UPDATE users
            SET password = ?
            WHERE id = ?
            """,
            (password_hash, user["id"]),
        )

        conn.commit()

        return jsonify(
            success=True,
            message="Password reset successful. Please login with your new password.",
        )

    except Exception as error:
        conn.rollback()

        print("FORGOT PASSWORD ERROR:", error)

        return jsonify(
            success=False,
            message="Something went wrong while resetting your password.",
        ), 500

    finally:
        conn.close()


@app.post("/api/logout")
def api_logout():
    session.clear()

    return jsonify(
        success=True,
        message="Logout successful.",
    )


@app.get("/api/me")
@login_required
def api_me():
    user = current_user()

    return jsonify(
        success=True,
        user={
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "mobile": user["mobile"],
            "created_at": user["created_at"],
        },
    )


# ============================================================
# USERS API
# ============================================================

@app.get("/api/users")
@login_required
def api_get_users():
    conn = get_db()

    try:
        rows = conn.execute(
            """
            SELECT id, name, email, mobile, created_at
            FROM users
            ORDER BY id DESC
            """
        ).fetchall()

        users = [
            {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "mobile": row["mobile"] or "",
                "created_at": row["created_at"],
            }
            for row in rows
        ]

        return jsonify(
            success=True,
            total_users=len(users),
            users=users,
        )
    finally:
        conn.close()


@app.post("/api/users")
@login_required
def api_create_user():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    mobile = str(data.get("mobile", "")).strip()
    password = str(data.get("password", ""))

    if not name or not email or not password:
        return jsonify(
            success=False,
            message="Name, email and password are required.",
        ), 400

    if len(password) < 6:
        return jsonify(
            success=False,
            message="Password must be at least 6 characters.",
        ), 400

    conn = get_db()

    try:
        cursor = conn.execute(
            """
            INSERT INTO users
            (name, email, mobile, password)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                mobile,
                generate_password_hash(password),
            ),
        )

        conn.commit()

        return jsonify(
            success=True,
            message="User created successfully.",
            user_id=cursor.lastrowid,
        ), 201

    except sqlite3.IntegrityError:
        return jsonify(
            success=False,
            message="Email already registered.",
        ), 409

    finally:
        conn.close()


@app.get("/api/users/<int:user_id>")
@login_required
def api_get_user(user_id):
    conn = get_db()

    try:
        user = conn.execute(
            """
            SELECT id, name, email, mobile, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if not user:
            return jsonify(
                success=False,
                message="User not found.",
            ), 404

        return jsonify(
            success=True,
            user=dict(user),
        )
    finally:
        conn.close()


@app.put("/api/users/<int:user_id>")
@login_required
def api_update_user(user_id):
    if user_id != session.get("user_id"):
        return jsonify(
            success=False,
            message="You can update only your own profile.",
        ), 403

    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    mobile = str(data.get("mobile", "")).strip()
    password = str(data.get("password", ""))

    if not name or not email:
        return jsonify(
            success=False,
            message="Name and email are required.",
        ), 400

    conn = get_db()

    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        if not existing:
            return jsonify(
                success=False,
                message="User not found.",
            ), 404

        if password:
            if len(password) < 6:
                return jsonify(
                    success=False,
                    message="Password must be at least 6 characters.",
                ), 400

            conn.execute(
                """
                UPDATE users
                SET name = ?, email = ?, mobile = ?, password = ?
                WHERE id = ?
                """,
                (
                    name,
                    email,
                    mobile,
                    generate_password_hash(password),
                    user_id,
                ),
            )
        else:
            conn.execute(
                """
                UPDATE users
                SET name = ?, email = ?, mobile = ?
                WHERE id = ?
                """,
                (
                    name,
                    email,
                    mobile,
                    user_id,
                ),
            )

        conn.commit()

        session["user_name"] = name
        session["user_email"] = email

        return jsonify(
            success=True,
            message="User updated successfully.",
        )

    except sqlite3.IntegrityError:
        return jsonify(
            success=False,
            message="Email already registered.",
        ), 409

    finally:
        conn.close()


@app.delete("/api/users/<int:user_id>")
@login_required
def api_delete_user(user_id):
    if user_id != session.get("user_id"):
        return jsonify(
            success=False,
            message="You can delete only your own account.",
        ), 403

    conn = get_db()

    try:
        user = conn.execute(
            "SELECT id FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        if not user:
            return jsonify(
                success=False,
                message="User not found.",
            ), 404

        conn.execute(
            """
            UPDATE surveys
            SET created_by = NULL
            WHERE created_by = ?
            """,
            (user_id,),
        )

        conn.execute(
            """
            UPDATE responses
            SET user_id = NULL
            WHERE user_id = ?
            """,
            (user_id,),
        )

        conn.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,),
        )

        conn.commit()
        session.clear()

        return jsonify(
            success=True,
            message="User deleted successfully.",
        )

    finally:
        conn.close()


# ============================================================
# DASHBOARD API
# ============================================================

@app.get("/api/dashboard")
@login_required
def api_dashboard():
    conn = get_db()

    try:
        total_users = conn.execute(
            "SELECT COUNT(*) AS count FROM users"
        ).fetchone()["count"]

        total_surveys = conn.execute(
            "SELECT COUNT(*) AS count FROM surveys"
        ).fetchone()["count"]

        active_surveys = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM surveys
            WHERE status IN ('active', 'published')
            """
        ).fetchone()["count"]

        draft_surveys = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM surveys
            WHERE status = 'draft'
            """
        ).fetchone()["count"]

        published_surveys = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM surveys
            WHERE status = 'published'
            """
        ).fetchone()["count"]

        total_responses = conn.execute(
            "SELECT COUNT(*) AS count FROM responses"
        ).fetchone()["count"]

        return jsonify(
            success=True,
            data={
                "total_users": total_users,
                "total_surveys": total_surveys,
                "active_surveys": active_surveys,
                "draft_surveys": draft_surveys,
                "published_surveys": published_surveys,
                "total_responses": total_responses,
            },
        )
    finally:
        conn.close()


# ============================================================
# SURVEY QUESTION SETTINGS
# ============================================================

ALLOWED_TYPES = {
    "multiple_choice",
    "short_answer",
    "rating_scale",
    "dropdown",
    "checkbox",
    "likert_scale",
}

OPTION_TYPES = {
    "multiple_choice",
    "rating_scale",
    "dropdown",
    "checkbox",
    "likert_scale",
}


def clean_question(item):
    if not isinstance(item, dict):
        return None, "Question data is invalid."

    text = str(item.get("question", "")).strip()

    question_type = str(
        item.get("question_type", "short_answer")
    ).strip().lower()

    if not text:
        return None, "Question text is required."

    if question_type not in ALLOWED_TYPES:
        return None, "Invalid question type."

    options = item.get("options", [])

    if not isinstance(options, list):
        options = []

    options = [
        str(option).strip()
        for option in options
        if str(option).strip()
    ]

    if question_type in OPTION_TYPES and not options:
        return None, "This question type needs options."

    return {
        "question": text,
        "question_type": question_type,
        "options": options,
        "required": 1 if item.get("required") else 0,
    }, None


def clean_questions(questions):
    if not isinstance(questions, list):
        return None, "Questions must be a list."

    if len(questions) != 6:
        return None, "Survey must contain exactly 6 questions."

    cleaned = []

    for index, item in enumerate(questions, 1):
        question, error = clean_question(item)

        if error:
            return None, f"Question {index}: {error}"

        cleaned.append(question)

    return cleaned, None


def insert_questions(conn, survey_id, questions):
    conn.execute(
        """
        DELETE FROM survey_questions
        WHERE survey_id = ?
        """,
        (survey_id,),
    )

    for order, question in enumerate(questions, 1):
        conn.execute(
            """
            INSERT INTO survey_questions
            (
                survey_id,
                question,
                question_type,
                options,
                required,
                question_order
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                survey_id,
                question["question"],
                question["question_type"],
                json.dumps(
                    question["options"],
                    ensure_ascii=False,
                ),
                question["required"],
                order,
            ),
        )


def serialize_question(row):
    try:
        options = json.loads(row["options"] or "[]")
    except Exception:
        options = []

    return {
        "id": row["id"],
        "question": row["question"],
        "question_type": row["question_type"],
        "options": options,
        "required": bool(row["required"]),
        "question_order": row["question_order"],
    }


# ============================================================
# CREATE SURVEY
# ============================================================

@app.post("/api/surveys")
@login_required
def api_create_survey():
    data = request.get_json(silent=True) or {}

    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()

    questions, error = clean_questions(
        data.get("questions", [])
    )

    if not title:
        return jsonify(
            success=False,
            message="Please enter a survey title.",
        ), 400

    if error:
        return jsonify(
            success=False,
            message=error,
        ), 400

    # --------------------------------------------------------
    # ANSWERS FROM ADD SURVEY
    # --------------------------------------------------------

    answers = data.get("answers", {})

    if not isinstance(answers, dict):
        return jsonify(
            success=False,
            message="Answers must be a JSON object.",
        ), 400

    required_answer_keys = [
        "q1",
        "q2",
        "q3",
        "q4",
        "q5",
        "q6",
    ]

    for key in required_answer_keys:
        if key not in answers:
            return jsonify(
                success=False,
                message=f"Answer for {key.upper()} is required.",
            ), 400

        value = answers.get(key)

        if value is None:
            return jsonify(
                success=False,
                message=f"Answer for {key.upper()} is required.",
            ), 400

        if isinstance(value, list):
            if len(value) == 0:
                return jsonify(
                    success=False,
                    message=f"Answer for {key.upper()} is required.",
                ), 400
        else:
            if str(value).strip() == "":
                return jsonify(
                    success=False,
                    message=f"Answer for {key.upper()} is required.",
                ), 400

    conn = get_db()

    try:
        cursor = conn.execute(
            """
            INSERT INTO surveys
            (title, description, created_by, status)
            VALUES (?, ?, ?, 'draft')
            """,
            (
                title,
                description,
                session["user_id"],
            ),
        )

        survey_id = cursor.lastrowid

        insert_questions(
            conn,
            survey_id,
            questions,
        )

        # ----------------------------------------------------
        # SAVE THE SELECTED ANSWERS AS A RESPONSE
        # ----------------------------------------------------

        user = current_user()

        user_name = ""
        user_email = ""

        if user:
            user_name = str(
                user["name"] or ""
            ).strip()

            user_email = str(
                user["email"] or ""
            ).strip().lower()

        conn.execute(
            """
            INSERT INTO responses
            (
                survey_id,
                user_id,
                name,
                email,
                answers
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                survey_id,
                session["user_id"],
                user_name,
                user_email,
                json.dumps(
                    answers,
                    ensure_ascii=False,
                ),
            ),
        )

        conn.commit()

        return jsonify(
            success=True,
            message="Survey saved as draft.",
            survey_id=survey_id,
        ), 201

    except Exception as e:
        conn.rollback()

        return jsonify(
            success=False,
            message=str(e),
        ), 500

    finally:
        conn.close()



# ============================================================
# GET ALL SURVEYS
# ============================================================

@app.get("/api/surveys")
@login_required
def api_get_surveys():
    conn = get_db()

    try:
        rows = conn.execute(
            """
            SELECT
                s.id,
                s.title,
                s.description,
                s.created_by,
                s.status,
                s.created_at,
                s.published_at,

                (
                    SELECT COUNT(*)
                    FROM survey_questions q
                    WHERE q.survey_id = s.id
                ) AS question_count,

                (
                    SELECT COUNT(*)
                    FROM responses r
                    WHERE r.survey_id = s.id
                ) AS response_count

            FROM surveys s
            ORDER BY s.id DESC
            """
        ).fetchall()

        surveys_list = [
            {
                "id": row["id"],
                "title": row["title"],
                "description": row["description"] or "",
                "created_by": row["created_by"],
                "status": row["status"] or "draft",
                "question_count": row["question_count"] or 0,
                "response_count": row["response_count"] or 0,
                "created_at": row["created_at"],
                "published_at": row["published_at"],
            }
            for row in rows
        ]

        return jsonify(
            success=True,
            total_surveys=len(surveys_list),
            surveys=surveys_list,
        )
    finally:
        conn.close()


# ============================================================
# GET ONE SURVEY
# ============================================================

@app.get("/api/surveys/<int:survey_id>")
@login_required
def api_get_survey(survey_id):
    """
    Get a survey for the logged-in user.

    The survey structure is returned for viewing/editing the form UI,
    but the answers returned here belong ONLY to the currently logged-in
    user. This prevents one user from loading another user's response
    into the Edit Survey page.
    """
    conn = get_db()

    try:
        survey = conn.execute(
            """
            SELECT
                id,
                title,
                description,
                created_by,
                status,
                created_at,
                published_at
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,),
        ).fetchone()

        if not survey:
            return jsonify(
                success=False,
                message="Survey not found.",
            ), 404

        question_rows = conn.execute(
            """
            SELECT
                id,
                question,
                question_type,
                options,
                required,
                question_order
            FROM survey_questions
            WHERE survey_id = ?
            ORDER BY question_order, id
            """,
            (survey_id,),
        ).fetchall()

        result = dict(survey)
        result["description"] = result["description"] or ""
        result["questions"] = [
            serialize_question(row)
            for row in question_rows
        ]

        # --------------------------------------------------------
        # IMPORTANT:
        # Load ONLY the logged-in user's own response.
        # --------------------------------------------------------
        own_response = conn.execute(
            """
            SELECT
                id,
                user_id,
                name,
                email,
                answers,
                submitted_at
            FROM responses
            WHERE survey_id = ?
              AND user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                survey_id,
                session["user_id"],
            ),
        ).fetchone()

        answers = {}

        if own_response:
            try:
                answers = json.loads(
                    own_response["answers"] or "{}"
                )
            except Exception:
                answers = {}

        result["answers"] = answers
        result["response_id"] = (
            own_response["id"]
            if own_response
            else None
        )
        result["response_owner_id"] = (
            own_response["user_id"]
            if own_response
            else None
        )
        result["response_owner_email"] = (
            own_response["email"]
            if own_response
            else None
        )

        return jsonify(
            success=True,
            survey=result,
        )

    finally:
        conn.close()


# ============================================================
# VIEW SURVEY / LATEST RESPONSE
# ============================================================

@app.get("/api/surveys/<int:survey_id>/view")
@login_required
def api_view_survey(survey_id):
    conn = get_db()

    try:
        survey = conn.execute(
            """
            SELECT id, title, description, status
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,),
        ).fetchone()

        if not survey:
            return jsonify(
                success=False,
                message="Survey not found.",
            ), 404

        response = conn.execute(
            """
            SELECT
                id,
                user_id,
                name,
                email,
                answers,
                submitted_at
            FROM responses
            WHERE survey_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (survey_id,),
        ).fetchone()

        question_rows = conn.execute(
            """
            SELECT
                id,
                question,
                question_type,
                options,
                required,
                question_order
            FROM survey_questions
            WHERE survey_id = ?
            ORDER BY question_order, id
            """,
            (survey_id,),
        ).fetchall()

        if response:
            try:
                answers = json.loads(
                    response["answers"] or "{}"
                )
            except Exception:
                answers = {}
        else:
            answers = {}

        question_list = []

        for row in question_rows:
            question_data = serialize_question(row)

            question_id = str(row["id"])
            answer = None

            if question_id in answers:
                answer = answers[question_id]
            elif str(row["question_order"]) in answers:
                answer = answers[str(row["question_order"])]
            elif f"q{row['question_order']}" in answers:
                answer = answers[f"q{row['question_order']}"]
            elif row["question"] in answers:
                answer = answers[row["question"]]

            question_data["answer"] = answer
            question_list.append(question_data)

        response_data = None

        if response:
            response_data = {
                "id": response["id"],
                "user_id": response["user_id"],
                "name": response["name"] or "",
                "email": response["email"] or "",
                "submitted_at": response["submitted_at"],
                "answers": answers,
            }

        return jsonify(
            success=True,
            survey={
                "id": survey["id"],
                "title": survey["title"],
                "description": survey["description"] or "",
                "status": survey["status"] or "draft",
            },
            response=response_data,
            questions=question_list,
        )

    finally:
        conn.close()


# ============================================================
# UPDATE SURVEY
# ============================================================

@app.put("/api/surveys/<int:survey_id>")
@login_required
def api_update_survey(survey_id):
    """
    Update ONLY the logged-in user's own response.

    Security rule:
        response.survey_id == survey_id
        AND
        response.user_id == session["user_id"]

    Therefore:
        - User A can edit only User A's response.
        - User B cannot edit User A's response.
        - Being the survey creator/owner alone does NOT grant access
          to edit somebody else's response.
    """
    data = request.get_json(silent=True) or {}

    answers = data.get("answers")

    if not isinstance(answers, dict):
        return jsonify(
            success=False,
            message="Answers must be a JSON object.",
        ), 400

    # ------------------------------------------------------------
    # Validate that the logged-in user has their OWN response.
    # ------------------------------------------------------------
    conn = get_db()

    try:
        survey = conn.execute(
            """
            SELECT id, title, description, status
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,),
        ).fetchone()

        if not survey:
            return jsonify(
                success=False,
                message="Survey not found.",
            ), 404

        own_response = conn.execute(
            """
            SELECT
                id,
                user_id,
                email
            FROM responses
            WHERE survey_id = ?
              AND user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                survey_id,
                session["user_id"],
            ),
        ).fetchone()

        # --------------------------------------------------------
        # CRITICAL SECURITY CHECK
        # --------------------------------------------------------
        if not own_response:
            return jsonify(
                success=False,
                message="You can edit only your own response.",
            ), 403

        # --------------------------------------------------------
        # Get the current logged-in user's real account details.
        # Do NOT trust name/email sent by the browser.
        # --------------------------------------------------------
        user = conn.execute(
            """
            SELECT id, name, email
            FROM users
            WHERE id = ?
            """,
            (session["user_id"],),
        ).fetchone()

        if not user:
            session.clear()

            return jsonify(
                success=False,
                message="Please login again.",
            ), 401

        # --------------------------------------------------------
        # Validate required answers against this survey's questions.
        # --------------------------------------------------------
        question_rows = conn.execute(
            """
            SELECT
                id,
                question,
                required,
                question_order
            FROM survey_questions
            WHERE survey_id = ?
            ORDER BY question_order, id
            """,
            (survey_id,),
        ).fetchall()

        missing = []

        for row in question_rows:
            if not row["required"]:
                continue

            question_id = str(row["id"])
            question_order = str(row["question_order"])

            value = answers.get(question_id)

            # Support the answer formats already used by this project:
            # question id, question order, and q1/q2... keys.
            if value is None:
                value = answers.get(question_order)

            if value is None:
                value = answers.get(
                    f"q{row['question_order']}"
                )

            if value is None:
                value = answers.get(row["question"])

            if value in (None, "", []):
                missing.append(row["question"])

        if missing:
            return jsonify(
                success=False,
                message="Please answer all required questions.",
                missing_questions=missing,
            ), 400

        # --------------------------------------------------------
        # UPDATE ONLY THIS USER'S RESPONSE.
        #
        # IMPORTANT:
        # We intentionally DO NOT update:
        #   surveys.title
        #   surveys.description
        #   survey_questions
        #
        # A respondent is allowed to edit their own answers only.
        # --------------------------------------------------------
        conn.execute(
            """
            UPDATE responses
            SET
                user_id = ?,
                name = ?,
                email = ?,
                answers = ?,
                submitted_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND survey_id = ?
              AND user_id = ?
            """,
            (
                user["id"],
                user["name"] or "",
                user["email"] or "",
                json.dumps(
                    answers,
                    ensure_ascii=False,
                ),
                own_response["id"],
                survey_id,
                session["user_id"],
            ),
        )

        conn.commit()

        return jsonify(
            success=True,
            message="Your response was updated successfully.",
            survey_id=survey_id,
            response_id=own_response["id"],
            user_id=session["user_id"],
        )

    except Exception as e:
        conn.rollback()

        return jsonify(
            success=False,
            message=str(e),
        ), 500

    finally:
        conn.close()


# ============================================================
# PUBLISH SURVEY
# ============================================================

@app.post("/api/surveys/<int:survey_id>/publish")
@login_required
def api_publish_survey(survey_id):
    conn = get_db()

    try:
        survey = conn.execute(
            """
            SELECT id, title, created_by, status
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,),
        ).fetchone()

        if not survey:
            return jsonify(
                success=False,
                message="Survey not found.",
            ), 404

        if survey["created_by"] != session["user_id"]:
            return jsonify(
                success=False,
                message="You cannot publish this survey.",
            ), 403

        if survey["status"] == "published":
            return jsonify(
                success=False,
                message="Survey is already published.",
            ), 400

        if survey["status"] == "closed":
            return jsonify(
                success=False,
                message="Closed survey cannot be published.",
            ), 400

        question_count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM survey_questions
            WHERE survey_id = ?
            """,
            (survey_id,),
        ).fetchone()["count"]

        if question_count != 6:
            return jsonify(
                success=False,
                message="Survey must contain exactly 6 questions.",
            ), 400

        conn.execute(
            """
            UPDATE surveys
            SET
                status = 'published',
                published_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (survey_id,),
        )

        conn.commit()

        total_responses = conn.execute(
            "SELECT COUNT(*) AS count FROM responses"
        ).fetchone()["count"]

        survey_response_count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM responses
            WHERE survey_id = ?
            """,
            (survey_id,),
        ).fetchone()["count"]

        return jsonify(
            success=True,
            message="Survey published successfully.",
            survey_id=survey_id,
            total_responses=total_responses,
            survey_response_count=survey_response_count,
        )

    except Exception as e:
        conn.rollback()

        print("PUBLISH ERROR:", e)

        return jsonify(
            success=False,
            message=str(e),
        ), 500

    finally:
        conn.close()


# ============================================================
# DELETE SURVEY
# ============================================================

@app.delete("/api/surveys/<int:survey_id>")
@login_required
def api_delete_survey(survey_id):
    conn = get_db()

    try:
        survey = conn.execute(
            """
            SELECT id, created_by
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,),
        ).fetchone()

        if not survey:
            return jsonify(
                success=False,
                message="Survey not found.",
            ), 404

        if survey["created_by"] != session["user_id"]:
            return jsonify(
                success=False,
                message="You cannot delete this survey.",
            ), 403

        conn.execute(
            "DELETE FROM responses WHERE survey_id = ?",
            (survey_id,),
        )

        conn.execute(
            "DELETE FROM survey_questions WHERE survey_id = ?",
            (survey_id,),
        )

        conn.execute(
            "DELETE FROM surveys WHERE id = ?",
            (survey_id,),
        )

        conn.commit()

        return jsonify(
            success=True,
            message="Survey deleted successfully.",
        )

    except Exception as e:
        conn.rollback()

        return jsonify(
            success=False,
            message=str(e),
        ), 500

    finally:
        conn.close()


# ============================================================
# QUESTIONS API
# ============================================================

@app.get("/api/surveys/<int:survey_id>/questions")
@login_required
def api_get_questions(survey_id):
    conn = get_db()

    try:
        survey = conn.execute(
            "SELECT id FROM surveys WHERE id = ?",
            (survey_id,),
        ).fetchone()

        if not survey:
            return jsonify(
                success=False,
                message="Survey not found.",
            ), 404

        rows = conn.execute(
            """
            SELECT
                id,
                question,
                question_type,
                options,
                required,
                question_order
            FROM survey_questions
            WHERE survey_id = ?
            ORDER BY question_order, id
            """,
            (survey_id,),
        ).fetchall()

        return jsonify(
            success=True,
            survey_id=survey_id,
            questions=[
                serialize_question(row)
                for row in rows
            ],
        )
    finally:
        conn.close()


@app.post("/api/surveys/<int:survey_id>/questions")
@login_required
def api_add_question(survey_id):
    data = request.get_json(silent=True) or {}

    conn = get_db()

    try:
        survey = conn.execute(
            """
            SELECT id, created_by, status
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,),
        ).fetchone()

        if not survey:
            return jsonify(
                success=False,
                message="Survey not found.",
            ), 404

        if survey["created_by"] != session["user_id"]:
            return jsonify(
                success=False,
                message="You cannot modify this survey.",
            ), 403

        count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM survey_questions
            WHERE survey_id = ?
            """,
            (survey_id,),
        ).fetchone()["count"]

        if count >= 6:
            return jsonify(
                success=False,
                message="Survey can contain exactly 6 questions.",
            ), 400

        question, error = clean_question(data)

        if error:
            return jsonify(
                success=False,
                message=error,
            ), 400

        cursor = conn.execute(
            """
            INSERT INTO survey_questions
            (
                survey_id,
                question,
                question_type,
                options,
                required,
                question_order
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                survey_id,
                question["question"],
                question["question_type"],
                json.dumps(
                    question["options"],
                    ensure_ascii=False,
                ),
                question["required"],
                count + 1,
            ),
        )

        conn.commit()

        return jsonify(
            success=True,
            message="Question added successfully.",
            question_id=cursor.lastrowid,
        ), 201

    except Exception as e:
        conn.rollback()

        return jsonify(
            success=False,
            message=str(e),
        ), 500

    finally:
        conn.close()


@app.put("/api/questions/<int:question_id>")
@login_required
def api_update_question(question_id):
    data = request.get_json(silent=True) or {}

    question, error = clean_question(data)

    if error:
        return jsonify(
            success=False,
            message=error,
        ), 400

    conn = get_db()

    try:
        row = conn.execute(
            """
            SELECT
                q.id,
                q.survey_id,
                s.created_by,
                s.status
            FROM survey_questions q
            JOIN surveys s
                ON s.id = q.survey_id
            WHERE q.id = ?
            """,
            (question_id,),
        ).fetchone()

        if not row:
            return jsonify(
                success=False,
                message="Question not found.",
            ), 404

        if row["created_by"] != session["user_id"]:
            return jsonify(
                success=False,
                message="You cannot update this question.",
            ), 403

        if row["status"] == "closed":
            return jsonify(
                success=False,
                message="Closed survey cannot be edited.",
            ), 400

        conn.execute(
            """
            UPDATE survey_questions
            SET
                question = ?,
                question_type = ?,
                options = ?,
                required = ?
            WHERE id = ?
            """,
            (
                question["question"],
                question["question_type"],
                json.dumps(
                    question["options"],
                    ensure_ascii=False,
                ),
                question["required"],
                question_id,
            ),
        )

        conn.commit()

        return jsonify(
            success=True,
            message="Question updated successfully.",
        )

    finally:
        conn.close()


@app.delete("/api/questions/<int:question_id>")
@login_required
def api_delete_question(question_id):
    conn = get_db()

    try:
        row = conn.execute(
            """
            SELECT
                q.id,
                q.survey_id,
                s.created_by,
                s.status
            FROM survey_questions q
            JOIN surveys s
                ON s.id = q.survey_id
            WHERE q.id = ?
            """,
            (question_id,),
        ).fetchone()

        if not row:
            return jsonify(
                success=False,
                message="Question not found.",
            ), 404

        if row["created_by"] != session["user_id"]:
            return jsonify(
                success=False,
                message="You cannot delete this question.",
            ), 403

        if row["status"] == "closed":
            return jsonify(
                success=False,
                message="Closed survey cannot be edited.",
            ), 400

        conn.execute(
            """
            DELETE FROM survey_questions
            WHERE id = ?
            """,
            (question_id,),
        )

        conn.execute(
            """
            UPDATE survey_questions
            SET question_order = (
                SELECT COUNT(*)
                FROM survey_questions q2
                WHERE q2.survey_id = survey_questions.survey_id
                  AND q2.id <= survey_questions.id
            )
            WHERE survey_id = ?
            """,
            (row["survey_id"],),
        )

        conn.commit()

        return jsonify(
            success=True,
            message="Question deleted successfully.",
        )

    finally:
        conn.close()


# ============================================================
# RESPONSES API
# ============================================================

@app.post("/api/responses")
@login_required
def api_submit_response():
    data = request.get_json(silent=True) or {}

    survey_id = data.get("survey_id")
    answers = data.get("answers")

    if not survey_id:
        return jsonify(
            success=False,
            message="survey_id is required.",
        ), 400

    if not isinstance(answers, dict):
        return jsonify(
            success=False,
            message="answers must be a JSON object.",
        ), 400

    conn = get_db()

    try:
        survey = conn.execute(
            """
            SELECT id, title, status
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,),
        ).fetchone()

        if not survey:
            return jsonify(
                success=False,
                message="Survey not found.",
            ), 404

        if survey["status"] != "published":
            return jsonify(
                success=False,
                message="Only published surveys can receive responses.",
            ), 400

        user = current_user()

        # Always use the authenticated account's identity.
        # Do not trust name/email supplied by the browser.
        name = str(
            user["name"] or ""
        ).strip()

        email = str(
            user["email"] or ""
        ).strip().lower()

        question_rows = conn.execute(
            """
            SELECT id, question, required
            FROM survey_questions
            WHERE survey_id = ?
            ORDER BY question_order, id
            """,
            (survey_id,),
        ).fetchall()

        missing = []

        for row in question_rows:
            if row["required"]:
                key = str(row["id"])

                if key not in answers or answers[key] in (
                    None,
                    "",
                    [],
                ):
                    missing.append(row["question"])

        if missing:
            return jsonify(
                success=False,
                message="Please answer all required questions.",
                missing_questions=missing,
            ), 400

        cursor = conn.execute(
            """
            INSERT INTO responses
            (
                survey_id,
                user_id,
                name,
                email,
                answers
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                survey_id,
                user["id"],
                name,
                email,
                json.dumps(
                    answers,
                    ensure_ascii=False,
                ),
            ),
        )

        conn.commit()

        return jsonify(
            success=True,
            message="Response submitted successfully.",
            response_id=cursor.lastrowid,
            survey_id=survey_id,
        ), 201

    except Exception as e:
        conn.rollback()

        return jsonify(
            success=False,
            message=str(e),
        ), 500

    finally:
        conn.close()


@app.get("/api/responses")
@login_required
def api_get_responses():
    conn = get_db()

    try:
        rows = conn.execute(
            """
            SELECT
                r.id,
                r.survey_id,
                r.user_id,
                r.name,
                r.email,
                r.submitted_at,
                s.title AS survey_title
            FROM responses r
            LEFT JOIN surveys s
                ON s.id = r.survey_id
            ORDER BY r.id DESC
            """
        ).fetchall()

        result = [
            {
                "id": row["id"],
                "survey_id": row["survey_id"],
                "user_id": row["user_id"],
                "survey_title": row["survey_title"] or "Survey",
                "name": row["name"] or "Unknown",
                "email": row["email"] or "Not available",
                "submitted_at": row["submitted_at"],
            }
            for row in rows
        ]

        return jsonify(
            success=True,
            total_responses=len(result),
            responses=result,
        )
    finally:
        conn.close()


@app.get("/api/responses/<int:response_id>")
@login_required
def api_get_single_response(response_id):
    conn = get_db()

    try:
        response = conn.execute(
            """
            SELECT
                r.id,
                r.survey_id,
                r.user_id,
                r.name,
                r.email,
                r.answers,
                r.submitted_at,
                s.title AS survey_title,
                s.description AS survey_description
            FROM responses r
            LEFT JOIN surveys s
                ON s.id = r.survey_id
            WHERE r.id = ?
            """,
            (response_id,),
        ).fetchone()

        if not response:
            return jsonify(
                success=False,
                message="Response not found.",
            ), 404

        try:
            answers = json.loads(
                response["answers"] or "{}"
            )
        except Exception:
            answers = {}

        question_rows = conn.execute(
            """
            SELECT
                id,
                question,
                question_type,
                options,
                required,
                question_order
            FROM survey_questions
            WHERE survey_id = ?
            ORDER BY question_order, id
            """,
            (response["survey_id"],),
        ).fetchall()

        questions = []

        for row in question_rows:
            question_data = serialize_question(row)

            question_id = str(row["id"])
            answer = None

            if question_id in answers:
                answer = answers[question_id]
            elif str(row["question_order"]) in answers:
                answer = answers[str(row["question_order"])]
            elif row["question"] in answers:
                answer = answers[row["question"]]

            question_data["answer"] = answer
            questions.append(question_data)

        return jsonify(
            success=True,
            response={
                "id": response["id"],
                "survey_id": response["survey_id"],
                "user_id": response["user_id"],
                "name": response["name"] or "",
                "email": response["email"] or "",
                "submitted_at": response["submitted_at"],
                "answers": answers,
            },
            survey={
                "title": response["survey_title"] or "Survey",
                "description": response["survey_description"] or "",
            },
            questions=questions,
        )

    finally:
        conn.close()


@app.delete("/api/responses/<int:response_id>")
@login_required
def api_delete_response(response_id):
    conn = get_db()

    try:
        response = conn.execute(
            """
            SELECT id
            FROM responses
            WHERE id = ?
            """,
            (response_id,),
        ).fetchone()

        if not response:
            return jsonify(
                success=False,
                message="Response not found.",
            ), 404

        conn.execute(
            "DELETE FROM responses WHERE id = ?",
            (response_id,),
        )

        conn.commit()

        return jsonify(
            success=True,
            message="Response deleted successfully.",
        )

    finally:
        conn.close()


@app.get("/api/surveys/<int:survey_id>/responses")
@login_required
def api_get_survey_responses(survey_id):
    conn = get_db()

    try:
        survey = conn.execute(
            "SELECT id, title FROM surveys WHERE id = ?",
            (survey_id,),
        ).fetchone()

        if not survey:
            return jsonify(
                success=False,
                message="Survey not found.",
            ), 404

        rows = conn.execute(
            """
            SELECT
                id,
                survey_id,
                user_id,
                name,
                email,
                submitted_at
            FROM responses
            WHERE survey_id = ?
            ORDER BY id DESC
            """,
            (survey_id,),
        ).fetchall()

        responses = [
            dict(row)
            for row in rows
        ]

        return jsonify(
            success=True,
            survey={
                "id": survey["id"],
                "title": survey["title"],
            },
            total_responses=len(responses),
            responses=responses,
        )

    finally:
        conn.close()


# ============================================================
# REPORTS / STATISTICS
# ============================================================

@app.get("/api/reports/survey/<int:survey_id>")
@login_required
def survey_report(survey_id):
    conn = get_db()

    try:
        survey = conn.execute(
            """
            SELECT
                id,
                title,
                description,
                status,
                created_at,
                published_at
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,),
        ).fetchone()

        if not survey:
            return jsonify(
                success=False,
                message="Survey not found.",
            ), 404

        total_responses = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM responses
            WHERE survey_id = ?
            """,
            (survey_id,),
        ).fetchone()["count"]

        total_questions = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM survey_questions
            WHERE survey_id = ?
            """,
            (survey_id,),
        ).fetchone()["count"]

        latest_response = conn.execute(
            """
            SELECT submitted_at
            FROM responses
            WHERE survey_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (survey_id,),
        ).fetchone()

        return jsonify(
            success=True,
            report={
                "survey": dict(survey),
                "total_questions": total_questions,
                "total_responses": total_responses,
                "latest_response": (
                    latest_response["submitted_at"]
                    if latest_response
                    else None
                ),
            },
        )

    finally:
        conn.close()


@app.get("/api/surveys/<int:survey_id>/statistics")
@app.get("/api/reports/survey/<int:survey_id>/statistics")
@login_required
def survey_statistics(survey_id):
    conn = get_db()

    try:
        survey = conn.execute(
            """
            SELECT id, title
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,),
        ).fetchone()

        if not survey:
            return jsonify(
                success=False,
                message="Survey not found.",
            ), 404

        total = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM responses
            WHERE survey_id = ?
            """,
            (survey_id,),
        ).fetchone()["count"]

        response_rows = conn.execute(
            """
            SELECT answers
            FROM responses
            WHERE survey_id = ?
            """,
            (survey_id,),
        ).fetchall()

        question_rows = conn.execute(
            """
            SELECT
                id,
                question,
                question_type,
                options,
                required,
                question_order
            FROM survey_questions
            WHERE survey_id = ?
            ORDER BY question_order, id
            """,
            (survey_id,),
        ).fetchall()

        statistics = []

        for question in question_rows:
            counts = {}

            for response in response_rows:
                try:
                    answers = json.loads(
                        response["answers"] or "{}"
                    )
                except Exception:
                    answers = {}

                key = str(question["id"])

                answer = answers.get(key)

                if answer is None:
                    answer = answers.get(
                        str(question["question_order"])
                    )

                if answer is None:
                    continue

                if isinstance(answer, list):
                    values = answer
                else:
                    values = [answer]

                for value in values:
                    value = str(value)

                    counts[value] = counts.get(value, 0) + 1

            statistics.append(
                {
                    "question_id": question["id"],
                    "question": question["question"],
                    "question_type": question["question_type"],
                    "total_answers": sum(counts.values()),
                    "answer_counts": counts,
                }
            )

        return jsonify(
            success=True,
            survey_id=survey_id,
            survey_title=survey["title"],
            total_responses=total,
            statistics=statistics,
        )

    finally:
        conn.close()


@app.get("/api/reports/survey/<int:survey_id>/export")
@login_required
def export_survey_report(survey_id):
    conn = get_db()

    try:
        survey = conn.execute(
            """
            SELECT id, title
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,),
        ).fetchone()

        if not survey:
            return jsonify(
                success=False,
                message="Survey not found.",
            ), 404

        rows = conn.execute(
            """
            SELECT
                id,
                survey_id,
                user_id,
                name,
                email,
                answers,
                submitted_at
            FROM responses
            WHERE survey_id = ?
            ORDER BY id ASC
            """,
            (survey_id,),
        ).fetchall()

        output = io.StringIO()

        writer = csv.writer(output)

        writer.writerow(
            [
                "Response ID",
                "Survey ID",
                "User ID",
                "Name",
                "Email",
                "Answers",
                "Submitted At",
            ]
        )

        for row in rows:
            writer.writerow(
                [
                    row["id"],
                    row["survey_id"],
                    row["user_id"],
                    row["name"] or "",
                    row["email"] or "",
                    row["answers"] or "{}",
                    row["submitted_at"] or "",
                ]
            )

        filename = (
            f"survey_{survey_id}_responses.csv"
        )

        response = make_response(
            output.getvalue()
        )

        response.headers["Content-Type"] = (
            "text/csv; charset=utf-8"
        )

        response.headers["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )

        return response

    finally:
        conn.close()


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify(
            success=False,
            message="API endpoint not found.",
        ), 404

    return """
    <h1>404 - Page Not Found</h1>
    """, 404


@app.errorhandler(500)
def server_error(error):
    if request.path.startswith("/api/"):
        return jsonify(
            success=False,
            message="Internal server error.",
        ), 500

    return """
    <h1>500 - Internal Server Error</h1>
    """, 500


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":
    init_db()

    app.run(
        debug=app.config["DEBUG"],
        host="127.0.0.1",
        port=5000,
    )