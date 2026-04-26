"""
E-ComSight — NLP Service
PhoBERT zero-shot + Rule-based fallback
"""
import re
import json
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ─── Rule-based Keywords Dictionary ───────────────────────────────────────────

POSITIVE_KEYWORDS = {
    "tốt", "hay", "tuyệt", "đẹp", "thích", "ưng", "ok", "ổn", "chất", "xịn",
    "đỉnh", "hoàn hảo", "hài lòng", "recommend", "ưa thích", "mượt", "mịn",
    "hiệu quả", "chuẩn", "xứng đáng", "chính hãng", "authentic", "thật",
    "giao nhanh", "đóng gói đẹp", "phục vụ tốt", "nhiệt tình", "dễ thương",
    "thơm", "nhẹ", "thẩm thấu", "không nhờn", "phù hợp", "da đẹp", "mịn da",
    "sáng da", "trị mụn", "hết mụn", "ẩm", "dưỡng tốt", "5 sao", "tuyệt vời",
    "xuất sắc", "vượt kỳ vọng", "ưu việt", "chuyên nghiệp", "giá tốt", "rẻ",
    "đúng mô tả", "y hình", "nhanh", "freeship", "quà tặng", "combo"
}

NEGATIVE_KEYWORDS = {
    "tệ", "kém", "xấu", "fake", "giả", "nhái", "lừa", "hàng giả", "không chính hãng",
    "kích ứng", "dị ứng", "đỏ mặt", "nổi mụn", "bỏng rát", "ngứa", "viêm",
    "giao muộn", "giao chậm", "hư", "vỡ", "móp", "không giống", "khác màu",
    "thất vọng", "không hài lòng", "phàn nàn", "tức", "tệ hại", "tránh",
    "không mua lại", "trả hàng", "hoàn tiền", "lừa đảo", "hàng nhái",
    "hết hạn", "quá hạn", "mùi lạ", "không thơm", "bết dính", "nhờn",
    "không hiệu quả", "vô dụng", "phản hồi chậm", "thiếu hàng", "nhầm hàng",
    "không đúng", "không đóng gói", "giao nhầm"
}

NEUTRAL_KEYWORDS = {
    "bình thường", "tạm ổn", "được", "tạm", "không có gì", "chưa dùng",
    "đang dùng thử", "xem thêm", "chờ xem", "chưa biết"
}

# Aspect keywords
ASPECT_KEYWORDS = {
    "product": {
        "chất lượng", "kết cấu", "mùi", "texture", "hiệu quả", "thành phần",
        "da", "mụn", "ẩm", "dưỡng", "sáng", "mịn", "hết", "thơm", "formula"
    },
    "shipping": {
        "giao", "vận chuyển", "shipper", "đóng gói", "hộp", "túi", "bọc",
        "nhanh", "chậm", "muộn", "trễ", "nguyên vẹn", "vỡ", "móp", "ngày"
    },
    "service": {
        "shop", "bán hàng", "phản hồi", "tư vấn", "chăm sóc", "đổi trả",
        "hoàn tiền", "nhiệt tình", "chuyên nghiệp", "hỗ trợ", "nhân viên"
    },
    "price": {
        "giá", "tiền", "rẻ", "đắt", "xứng đáng", "hời", "sale", "giảm giá",
        "khuyến mại", "freeship", "phí ship", "combo", "deal"
    }
}

# Urgency: Critical keywords
CRITICAL_KEYWORDS = {
    "hàng giả", "hàng nhái", "kích ứng", "dị ứng", "bỏng rát",
    "ngứa rát", "viêm da", "lừa đảo", "gian lận", "quá hạn", "hết hạn sử dụng",
    "độc hại", "gây hại", "fake 100%", "nhái hoàn toàn"
}
HIGH_KEYWORDS = {
    "chất lượng kém", "không hiệu quả", "giao chậm quá", "vỡ hết",
    "không giống ảnh", "nhầm hàng", "mất tiền", "thất vọng hoàn toàn"
}

# ─── PhoBERT Model (lazy load) ─────────────────────────────────────────────────

_model = None
_tokenizer = None


def load_phobert_model():
    global _model, _tokenizer
    if _model is None:
        try:
            logger.info("Đang load PhoBERT model...")
            from transformers import pipeline
            # wonrax/phobert-base-vietnamese-sentiment
            # Labels: NEG=0, NEU=1, POS=2
            _model = pipeline(
                "text-classification",
                model="wonrax/phobert-base-vietnamese-sentiment",
                return_all_scores=True,
                device=-1  # CPU
            )
            logger.info("✅ PhoBERT model loaded!")
        except Exception as e:
            logger.error(f"❌ Không load được PhoBERT: {e}")
            _model = None
    return _model


# ─── Core Analysis Functions ───────────────────────────────────────────────────

def preprocess_text(text: str) -> str:
    """Tiền xử lý text tiếng Việt"""
    if not text:
        return ""

    # Chuẩn hóa Unicode
    import unicodedata
    text = unicodedata.normalize("NFC", text)

    # Chuẩn hóa emoji → text
    emoji_map = {
        "😊": " vui ", "😍": " thích ", "❤️": " yêu ", "👍": " tốt ",
        "😡": " tức giận ", "👎": " không tốt ", "😢": " buồn ",
        "⭐": " sao ", "🔥": " hot ", "✅": " ok ", "❌": " không ",
        "🥰": " thích ", "😤": " bực ", "💯": " tuyệt ",
    }
    for emoji, replacement in emoji_map.items():
        text = text.replace(emoji, replacement)

    # Lowercase
    text = text.lower()

    # Teencode chuẩn hóa
    teencode_map = {
        "sp": "sản phẩm", "mk": "mình", "m": "mình",
        "ok": "ổn", "dc": "được", "đc": "được",
        "vs": "với", "cx": "cũng", "k": "không", "ko": "không",
        "nt": "nhắn tin", "bb": "baby", "bt": "bình thường",
        "ntn": "như thế nào", "qc": "quảng cáo", "cl": "chất lượng",
        "hsd": "hạn sử dụng", "tmdt": "thương mại điện tử",
    }
    words = text.split()
    words = [teencode_map.get(w, w) for w in words]
    text = " ".join(words)

    # Loại ký tự đặc biệt thừa
    text = re.sub(r"[^\w\s\u00C0-\u024F\u1E00-\u1EFF]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def rule_based_sentiment(text: str) -> dict:
    """Phân tích sentiment bằng rule-based keywords"""
    text_lower = text.lower()
    words = set(text_lower.split())

    # Đếm keywords
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text_lower)
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_lower)
    neu_count = sum(1 for kw in NEUTRAL_KEYWORDS if kw in text_lower)

    # Negation detection (không tốt → negative)
    negation_words = {"không", "chẳng", "chả", "ko", "k"}
    has_negation = any(w in words for w in negation_words)

    if has_negation and pos_count > 0:
        neg_count += pos_count
        pos_count = max(0, pos_count - 1)

    total = pos_count + neg_count + neu_count + 1
    pos_score = pos_count / total
    neg_score = neg_count / total

    if neg_count > pos_count:
        return {"label": "negative", "score": min(0.95, 0.5 + neg_score), "source": "rule"}
    elif pos_count > neg_count:
        return {"label": "positive", "score": min(0.95, 0.5 + pos_score), "source": "rule"}
    else:
        return {"label": "neutral", "score": 0.6, "source": "rule"}


def phobert_sentiment(text: str) -> Optional[dict]:
    """Phân tích sentiment bằng PhoBERT"""
    model = load_phobert_model()
    if model is None:
        return None

    try:
        # Truncate nếu quá dài
        if len(text) > 512:
            text = text[:512]

        results = model(text)
        if results and results[0]:
            # results[0] là list [{label, score}, ...]
            scores = {r["label"]: r["score"] for r in results[0]}

            # wonrax model labels: NEG, NEU, POS
            label_map = {"NEG": "negative", "NEU": "neutral", "POS": "positive"}

            best_label = max(scores, key=scores.get)
            return {
                "label": label_map.get(best_label, "neutral"),
                "score": scores[best_label],
                "all_scores": {label_map.get(k, k): v for k, v in scores.items()},
                "source": "phobert"
            }
    except Exception as e:
        logger.error(f"PhoBERT prediction error: {e}")
    return None


def detect_aspect(text: str) -> str:
    """Phát hiện aspect chính của review"""
    text_lower = text.lower()
    scores = {}

    for aspect, keywords in ASPECT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[aspect] = score

    if max(scores.values()) == 0:
        return "product"  # default

    return max(scores, key=scores.get)


def detect_urgency(text: str, sentiment: str) -> str:
    """Phát hiện mức độ khẩn cấp"""
    text_lower = text.lower()

    if any(kw in text_lower for kw in CRITICAL_KEYWORDS):
        return "critical"
    if any(kw in text_lower for kw in HIGH_KEYWORDS):
        return "high"
    if sentiment == "negative":
        return "medium"
    return "low"


def analyze_review(text: str, use_phobert: bool = True) -> dict:
    """
    Pipeline phân tích hoàn chỉnh:
    1. Preprocess
    2. PhoBERT zero-shot (nếu model available)
    3. Fallback rule-based
    4. Aspect detection
    5. Urgency detection
    """
    processed = preprocess_text(text)

    # Step 1: Thử PhoBERT
    result = None
    if use_phobert and processed:
        result = phobert_sentiment(processed)

    # Step 2: Fallback rule-based
    rule_result = rule_based_sentiment(processed)

    if result is None:
        result = rule_result
    else:
        # Ensemble: nếu độ tin cậy PhoBERT thấp, ưu tiên rule-based
        if result["score"] < 0.6 and rule_result["score"] > 0.7:
            result = rule_result
        elif result["score"] < 0.5:
            # Combine
            result["source"] = "ensemble"

    # Step 3: Aspect + Urgency
    aspect = detect_aspect(text)
    urgency = detect_urgency(text, result["label"])

    return {
        "sentiment_label": result["label"],
        "sentiment_score": round(result["score"], 4),
        "sentiment_source": result.get("source", "model"),
        "aspect_label": aspect,
        "urgency_label": urgency,
        "all_scores": result.get("all_scores", {}),
        "processed_text": processed,
        "analyzed_at": datetime.utcnow().isoformat(),
    }


def analyze_url(url: str) -> dict:
    """
    Phân tích URL sản phẩm Shopee/TikTok:
    - Xác định platform
    - Extract product ID
    - Lấy reviews từ API
    - Phân tích sentiment
    """
    result = {
        "platform": "unknown",
        "product_id": None,
        "reviews": [],
        "summary": {}
    }

    if "shopee.vn" in url:
        result["platform"] = "shopee"
        # Extract item ID từ URL Shopee
        match = re.search(r"i\.(\d+)\.(\d+)", url)
        if match:
            shopid, itemid = match.group(1), match.group(2)
            result["product_id"] = itemid
            result["shop_id"] = shopid
            # Fetch reviews
            try:
                import requests
                params = {
                    "itemid": itemid, "shopid": shopid,
                    "limit": 50, "offset": 0, "type": 0
                }
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://shopee.vn/"
                }
                resp = requests.get(
                    "https://shopee.vn/api/v2/item/get_ratings",
                    params=params, headers=headers, timeout=15
                )
                if resp.status_code == 200:
                    data = resp.json()
                    ratings = data.get("data", {}).get("ratings", []) or []
                    for r in ratings[:30]:  # Top 30 reviews
                        comment = r.get("comment", "").strip()
                        if comment:
                            analysis = analyze_review(comment)
                            result["reviews"].append({
                                "comment": comment,
                                "rating_star": r.get("rating_star", 0),
                                **analysis
                            })
            except Exception as e:
                logger.error(f"URL analysis error: {e}")

    elif "tiktok.com" in url or "tiktokshop" in url:
        result["platform"] = "tiktok"
        # TikTok URL parsing would go here

    # Summary
    if result["reviews"]:
        sentiments = [r["sentiment_label"] for r in result["reviews"]]
        result["summary"] = {
            "total": len(sentiments),
            "positive": sentiments.count("positive"),
            "neutral": sentiments.count("neutral"),
            "negative": sentiments.count("negative"),
            "positive_pct": round(sentiments.count("positive") / len(sentiments) * 100, 1),
        }

    return result
