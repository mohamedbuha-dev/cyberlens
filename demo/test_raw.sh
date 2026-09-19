#!/usr/bin/env bash
# اختبار سريع للعيّنات عبر نقطة /api/analyze/raw — يعرض الدرجة والمستوى فورًا
# دون الحاجة لحساب Gmail أو انتظار البوابة. مفيد للتجربة قبل العرض.
#
#   bash demo/test_raw.sh
#
set -euo pipefail

API="${API:-http://localhost:8081/api/analyze/raw}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for eml in "$HERE"/samples/*.eml; do
  name="$(basename "$eml")"
  result="$(curl -s -X POST "$API" -H "Content-Type: text/plain" --data-binary "@$eml" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d['risk_score'])+'%  '+d['risk_level'])")"
  printf "%-18s → %s\n" "$name" "$result"
done
