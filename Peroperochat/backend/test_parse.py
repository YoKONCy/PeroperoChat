import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from Peroperochat.backend.app.memory_service import parse_triggers_from_text

s = 'hello [[MEMTRG]]{"事件记录触发器": true, "用户爱好记录触发器": false, "助手爱好记录触发器": true}[[/MEMTRG]]'
print(parse_triggers_from_text(s))
