with open('frontend/components/temporal/TimeSeriesPlayer.tsx', 'r', encoding='utf-8') as f:
    c = f.read().replace('\r\n', '\n')

old = """  CheckCircle2,
  AlertCircle,
} from "lucide-react";"""

new = """  CheckCircle2,
  AlertCircle,
  XCircle,
} from "lucide-react";"""

assert old in c, "Target not found"
c = c.replace(old, new)
with open('frontend/components/temporal/TimeSeriesPlayer.tsx', 'w', encoding='utf-8') as f:
    f.write(c)
print("XCircle imported successfully")
