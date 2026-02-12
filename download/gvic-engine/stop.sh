#!/bin/bash

#####################################################
# GVIC Engine 중지 스크립트
#####################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}GVIC Engine 프로세스를 중지합니다...${NC}"

# Backend 프로세스 종료
if pgrep -f "uvicorn server:app" > /dev/null; then
    pkill -f "uvicorn server:app"
    echo -e "  ${GREEN}✓${NC} Backend 서버 종료됨"
else
    echo -e "  ${YELLOW}!${NC} Backend 서버가 실행 중이지 않습니다"
fi

# Frontend 프로세스 종료
if pgrep -f "react-scripts start" > /dev/null; then
    pkill -f "react-scripts start"
    echo -e "  ${GREEN}✓${NC} Frontend 서버 종료됨"
elif pgrep -f "craco start" > /dev/null; then
    pkill -f "craco start"
    echo -e "  ${GREEN}✓${NC} Frontend 서버 종료됨"
else
    echo -e "  ${YELLOW}!${NC} Frontend 서버가 실행 중이지 않습니다"
fi

echo ""
echo -e "${GREEN}완료.${NC}"
