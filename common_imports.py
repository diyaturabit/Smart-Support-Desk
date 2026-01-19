# common_imports.py
from database_connectivity.db_utils import execute_query
from decorators import jwt_required, admin_required
from exceptions import handle_exception
from logs.activity_logger import log_activity
from Redis.connection import get_cache, set_cache, delete_cache
from schemas import TicketCreate, TicketResponse, TicketUpdate,CustomerCreate,CustomerResponse
import mysql.connector
from flask import Blueprint, request, jsonify
from pydantic import ValidationError