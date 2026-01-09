import redis
import json
from flask import jsonify
rd=redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

def get_cache(key):
    data=rd.get(key)
    return json.loads(data) if data else None

def set_cache(key,value,ttl=100):
    rd.setex(key,ttl,json.dumps(value))

def delete_cache(key):
    rd.delete(key)
    
