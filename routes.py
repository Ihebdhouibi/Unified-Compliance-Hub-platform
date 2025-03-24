from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db

import json
import logging


@app.route("/")
def index():
    """Home page route"""
    return render_template("index.html")
