"""
GVIC 이미지 OCR 처리 모듈
- 이미지 파일에서 텍스트 추출 (Gemini Vision)
- 추출된 텍스트를 시그널로 변환
- 다양한 이미지 형식 지원 (PNG, JPG, JPEG, WEBP, GIF)
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import base64
import logging
import os
import uuid

router = APIRouter(prefix="/api/ocr", tags=["ocr"])
logger = logging.getLogger(__name__)

# 지원 이미지 형식
SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class OCRResult(BaseModel):
    """OCR 결과"""
    success: bool
    extracted_text: str
    confidence: float
    language: str
    text_blocks: List[Dict[str, Any]]
    image_description: str

async def extract_text_from_image(
    image_data: bytes,
    filename: str,
    purpose: str = ""
) -> Dict[str, Any]:
    """
    Gemini Vision을 사용하여 이미지에서 텍스트 추출
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="OCR 서비스가 설정되지 않았습니다")
    
    # 이미지를 base64로 인코딩
    image_base64 = base64.b64encode(image_data).decode("utf-8")
    
    # 파일 확장자로 MIME 타입 결정
    ext = os.path.splitext(filename)[1].lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp"
    }
    mime_type = mime_types.get(ext, "image/png")
    
    ocr_prompt = f"""이 이미지를 분석하고 다음 정보를 JSON 형식으로 추출해주세요:

1. 이미지에 포함된 모든 텍스트를 정확하게 추출
2. 텍스트의 언어 감지
3. 이미지 내용에 대한 간략한 설명
4. 텍스트 추출의 신뢰도 (0-1)

{f"분석 목적: {purpose}" if purpose else ""}

다음 JSON 형식으로 응답해주세요:
{{
    "extracted_text": "이미지에서 추출한 전체 텍스트 (줄바꿈 유지)",
    "text_blocks": [
        {{"text": "텍스트 블록 1", "position": "위치 설명"}},
        {{"text": "텍스트 블록 2", "position": "위치 설명"}}
    ],
    "language": "감지된 언어 (ko/en/etc)",
    "confidence": 0.0-1.0,
    "image_description": "이미지 내용 설명"
}}

텍스트가 없는 이미지인 경우 extracted_text를 빈 문자열로, confidence를 0으로 설정하세요."""

    try:
        llm = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"ocr-{uuid.uuid4().hex[:8]}",
            system_message="You are an OCR expert that extracts text from images and returns results in JSON format."
        ).with_model("gemini", "gemini-2.0-flash")
        
        # 이미지와 함께 메시지 전송
        response = await llm.send_message(
            UserMessage(
                text=ocr_prompt,
                images=[f"data:{mime_type};base64,{image_base64}"]
            )
        )
        
        response_text = response.strip()
        
        # JSON 파싱
        import json
        import re
        
        # JSON 블록 추출
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```") and not in_json:
                    in_json = True
                    continue
                elif line.startswith("```") and in_json:
                    break
                elif in_json:
                    json_lines.append(line)
            response_text = "\n".join(json_lines)
        
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            ocr_result = json.loads(json_match.group())
        else:
            # JSON 파싱 실패 시 전체 응답을 텍스트로 사용
            ocr_result = {
                "extracted_text": response_text,
                "text_blocks": [],
                "language": "unknown",
                "confidence": 0.5,
                "image_description": "텍스트 추출 결과"
            }
        
        return {
            "success": True,
            "extracted_text": ocr_result.get("extracted_text", ""),
            "text_blocks": ocr_result.get("text_blocks", []),
            "language": ocr_result.get("language", "unknown"),
            "confidence": ocr_result.get("confidence", 0.5),
            "image_description": ocr_result.get("image_description", ""),
            "filename": filename,
            "file_size": len(image_data)
        }
        
    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise HTTPException(status_code=500, detail=f"OCR 처리 중 오류: {str(e)}")


@router.post("/extract")
async def extract_text_endpoint(
    file: UploadFile = File(...),
    purpose: str = Form("")
):
    """
    이미지 파일에서 텍스트 추출 (OCR)
    
    지원 형식: PNG, JPG, JPEG, WEBP, GIF, BMP
    최대 파일 크기: 10MB
    """
    # 파일 형식 검증
    filename = file.filename or "image.png"
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400, 
            detail=f"지원하지 않는 형식입니다. 지원 형식: {', '.join(SUPPORTED_FORMATS)}"
        )
    
    # 파일 읽기
    image_data = await file.read()
    
    # 파일 크기 검증
    if len(image_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # OCR 수행
    result = await extract_text_from_image(image_data, filename, purpose)
    
    return result


@router.post("/extract-and-analyze")
async def extract_and_analyze_endpoint(
    file: UploadFile = File(...),
    purpose: str = Form(""),
    analysis_type: str = Form("general"),
    authorization: str = Depends(lambda: None)
):
    """
    이미지에서 텍스트 추출 후 GVIC 시그널로 분석
    
    1. OCR로 텍스트 추출
    2. 추출된 텍스트를 시그널로 생성
    3. GVIC 분석 (5:3:2 결이론, 크로스 분석, 가치 평가)
    """
    from signal_ingest import ingest_text_signal, TextSignalRequest
    from server import db
    
    # 파일 형식 검증
    filename = file.filename or "image.png"
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400, 
            detail=f"지원하지 않는 형식입니다. 지원 형식: {', '.join(SUPPORTED_FORMATS)}"
        )
    
    # 파일 읽기
    image_data = await file.read()
    
    if len(image_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # OCR 수행
    ocr_result = await extract_text_from_image(image_data, filename, purpose)
    
    extracted_text = ocr_result.get("extracted_text", "")
    
    if not extracted_text.strip():
        return {
            "success": True,
            "ocr_result": ocr_result,
            "signal_created": False,
            "message": "이미지에서 텍스트를 찾을 수 없습니다."
        }
    
    # OCR 결과 저장
    ocr_id = f"OCR_{uuid.uuid4().hex[:12]}"
    ocr_record = {
        "ocr_id": ocr_id,
        "filename": filename,
        "file_size": len(image_data),
        "extracted_text": extracted_text,
        "confidence": ocr_result.get("confidence", 0),
        "language": ocr_result.get("language", "unknown"),
        "image_description": ocr_result.get("image_description", ""),
        "purpose": purpose,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.ocr_results.insert_one(ocr_record)
    
    # 시그널 생성을 위한 콘텐츠 구성
    signal_content = f"[이미지 OCR 추출]\n"
    signal_content += f"파일: {filename}\n"
    if ocr_result.get("image_description"):
        signal_content += f"이미지 설명: {ocr_result['image_description']}\n"
    signal_content += f"\n추출된 텍스트:\n{extracted_text}"
    
    # AI 분석 수행
    from core.ai_analyzer import analyze_signal
    ai_result = await analyze_signal(
        content=signal_content,
        purpose=purpose,
        expected_result="이미지에서 추출된 텍스트 분석",
        analysis_type=analysis_type
    )
    
    # 파이프라인으로 시그널 생성
    from server import get_pipeline_engine
    pipeline = get_pipeline_engine()
    
    signal_result = await pipeline.create_signal(
        signal_type="image_ocr",
        content=signal_content,
        source=f"ocr:{filename}",
        metadata={
            "input_method": "image_ocr",
            "ocr_id": ocr_id,
            "filename": filename,
            "ocr_confidence": ocr_result.get("confidence", 0),
            "language": ocr_result.get("language", "unknown"),
            "image_description": ocr_result.get("image_description", ""),
            "purpose": purpose,
            "analysis_type": analysis_type,
            "ai_analysis": ai_result
        },
        user_id="system"  # TODO: 실제 사용자 ID
    )
    
    # GVIC 분석 수행
    try:
        from gvic_analyzer import analyze_with_gvic_lens, cross_analyze_signal, evaluate_asset_value
        
        # 5:3:2 결이론 분석
        gvic_result = await analyze_with_gvic_lens(
            content=signal_content,
            ai_analysis=ai_result,
            purpose=purpose
        )
        
        # 크로스 분석
        keywords = ai_result.get("keywords", [])
        category = ai_result.get("signal_category", "general")
        
        cross_result = await cross_analyze_signal(
            signal_id=signal_result.get("signal_id"),
            content=signal_content,
            keywords=keywords,
            category=category,
            max_related=5
        )
        
        # 가치 평가
        valuation_result = await evaluate_asset_value(
            content=signal_content,
            keywords=keywords,
            category=category
        )
        
        signal_result["gvic_analysis"] = gvic_result
        signal_result["cross_analysis"] = cross_result
        signal_result["asset_valuation"] = valuation_result
        
    except Exception as e:
        logger.error(f"GVIC analysis error for OCR: {e}")
    
    return {
        "success": True,
        "ocr_result": ocr_result,
        "signal_created": True,
        "signal_id": signal_result.get("signal_id"),
        "ai_analysis": ai_result,
        "gvic_analysis": signal_result.get("gvic_analysis"),
        "cross_analysis": signal_result.get("cross_analysis"),
        "asset_valuation": signal_result.get("asset_valuation"),
        "message": f"이미지에서 {len(extracted_text)}자의 텍스트를 추출하고 분석했습니다."
    }


@router.get("/history")
async def get_ocr_history(limit: int = 20):
    """OCR 처리 이력 조회"""
    from server import db
    
    results = await db.ocr_results.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "success": True,
        "total": len(results),
        "results": results
    }
