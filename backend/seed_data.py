"""
E-ComSight — Seed Data
Tạo dữ liệu mẫu để demo
"""
import sys
sys.path.insert(0, ".")

from app.database import SessionLocal, User, Review, Alert, create_tables
from app.routers.auth import hash_password
from app.services.nlp_service import analyze_review
from datetime import datetime, timedelta
import random

SAMPLE_REVIEWS = [
    # POSITIVE reviews mỹ phẩm
    ("positive", "shopee", "CeraVe Hydrating Cleanser", 5, "Sản phẩm tuyệt vời luôn, dùng 2 tuần da mình sạch mịn hơn hẳn. Shop đóng gói cẩn thận, giao nhanh lắm chỉ 1 ngày là có hàng. Sẽ mua lại lần 2 chắc chắn rồi!", "product"),
    ("positive", "shopee", "La Roche-Posay Effaclar", 5, "Kem rửa mặt này hoàn hảo cho da dầu mụn của mình. Sau 1 tháng dùng mụn giảm rõ ràng, da sáng và không bị khô căng sau khi rửa. Hàng chính hãng có seal đầy đủ.", "product"),
    ("positive", "tiktok", "Innisfree Green Tea Serum", 5, "Serum trà xanh này ngon lắm bạn ơi 😍 Texture mỏng nhẹ, thẩm thấu nhanh, mùi thơm dịu nhẹ tự nhiên. Da mình ẩm và mịn hơn sau 3 ngày dùng liên tục. Recommend 10/10!", "product"),
    ("positive", "shopee", "Some By Mi AHA BHA Toner", 5, "Freeship lại còn được tặng thêm sample nữa, shop quá xịn! Toner này dùng thấy lỗ chân lông se khít lại, da tone đều hơn. Đã mua lần 3 rồi không thể thiếu.", "product"),
    ("positive", "tiktok", "Anessa Perfect UV Sunscreen", 5, "Kem chống nắng nhẹ không bết dính, không để lại vệt trắng, phù hợp cho mùa hè oi bức. Giao hàng TikTok cũng nhanh, đóng gói an toàn. 5 sao không cần suy nghĩ.", "shipping"),
    ("positive", "shopee", "Klairs Supple Toner", 5, "Shop tư vấn nhiệt tình, giải đáp mọi thắc mắc rất nhanh. Sản phẩm y như mô tả, scan mã QR ra kết quả hàng thật. Giá tốt hơn mua ngoài tiệm 30%.", "service"),
    ("positive", "shopee", "Missha Time Revolution", 4, "Essence dưỡng ẩm tốt, da mình cảm thấy ẩm mượt cả ngày. Đóng gói đẹp, hàng nguyên vẹn không bị vỡ. Trừ 1 sao vì giao hơi chậm hơn dự kiến 1 ngày.", "product"),
    ("positive", "tiktok", "The Ordinary Niacinamide", 5, "Serum niacinamide này quá xịn, lỗ chân lông thật sự mờ đi sau 2 tuần. Giá rẻ hơn ở ngoài shop rất nhiều, hàng authentic 100%. Đã tặng cho 3 bạn bè rồi.", "price"),

    # NEGATIVE reviews
    ("negative", "shopee", "Kem dưỡng XYZ Brand", 1, "Hàng nhận về bị kích ứng ngay lần đầu dùng thử. Mặt mình đỏ ửng và ngứa ran, phải rửa lại ngay và ngưng dùng. Shop không phản hồi tin nhắn hỏi đổi trả. Rất thất vọng!", "product"),
    ("negative", "shopee", "Serum Vitamin C No-name", 2, "Giao hàng chậm quá, đặt 7 ngày mới tới trong khi ghi là 2-3 ngày làm việc. Hộp bị móp méo, may là chai serum chưa vỡ. Sản phẩm dùng thấy không hiệu quả như quảng cáo.", "shipping"),
    ("negative", "tiktok", "Kem Trị Mụn ABC", 1, "Nghi ngờ hàng giả vì mùi khác lạ hoàn toàn so với hàng chính hãng mình đã từng dùng. Scan QR code không ra kết quả. Shop bán hàng không uy tín, cần thận mọi người ơi!", "product"),
    ("negative", "shopee", "Toner Dưỡng Ẩm DEF", 2, "Shop giao nhầm hàng, mình đặt toner dưỡng ẩm nhưng nhận được loại khác hoàn toàn. Nhắn tin cho shop thì mãi 2 ngày sau mới phản hồi, giải quyết đổi trả rất chậm chạp.", "service"),
    ("negative", "tiktok", "Kem Chống Nắng GHI", 1, "Sản phẩm hết hạn sử dụng mà shop vẫn bán! Kiểm tra kỹ mọi người nhé. Mình may phát hiện trước khi dùng. Đề nghị TikTok kiểm tra shop này ngay!", "product"),
    ("negative", "shopee", "Sữa Dưỡng Thể JKL", 2, "Chất lượng không như hình ảnh quảng cáo. Texture đặc nhờn, khó thẩm thấu, để lại cảm giác bết dính khó chịu cả ngày. Mùi hắc, không dễ chịu như mô tả. Không mua lại.", "product"),
    ("negative", "shopee", "Mask Dưỡng Da MNO", 1, "Bị dị ứng nặng sau khi dùng mặt nạ này. Mặt mình nổi mẩn đỏ, sưng phù và ngứa rát. Phải đến bác sĩ da liễu. Shop không chịu nhận lỗi và hoàn tiền. Rất nguy hiểm!", "product"),

    # NEUTRAL reviews
    ("neutral", "shopee", "Toner PQR Brand", 3, "Sản phẩm tạm ổn, không thấy khác biệt nhiều so với các toner khác cùng tầm giá. Giao hàng đúng hẹn, đóng gói bình thường. Sẽ dùng thử thêm 1 tháng xem sao.", "product"),
    ("neutral", "tiktok", "Serum STU Brand", 3, "Bình thường thôi, không có gì nổi bật. Mua về để thử vì thấy TikTok review nhiều. Chưa thấy hiệu quả rõ ràng sau 1 tuần, chờ xem tiếp.", "product"),
    ("neutral", "shopee", "Kem Dưỡng VWX", 3, "Sản phẩm được thôi, không xuất sắc không tệ. Giao đúng thời gian, đóng gói ổn. Giá hơi cao so với chất lượng nhưng chấp nhận được.", "price"),
]

CRITICAL_REVIEWS = [
    ("negative", "shopee", "Kem trị mụn No-Brand", 1, "CẢNH BÁO: Sản phẩm này gây kích ứng nghiêm trọng! Mặt mình nổi mẩn đỏ toàn mặt sau 30 phút dùng. Tôi đã phải vào viện cấp cứu. Nghi ngờ hàng giả chứa thành phần độc hại!", "product"),
    ("negative", "tiktok", "Serum làm trắng da", 1, "Phát hiện hàng giả 100%! Bao bì giống nhưng mùi và màu sắc sản phẩm hoàn toàn khác. Shop này bán hàng nhái, mọi người tránh xa!", "product"),
]


def seed_database():
    create_tables()
    db = SessionLocal()

    try:
        # Tạo user demo
        if not db.query(User).filter(User.username == "demo").first():
            user = User(
                username="demo",
                email="demo@ecomsight.vn",
                hashed_password=hash_password("demo1234"),
                full_name="Nguyễn Hoàng Long",
                shop_name="Mỹ Phẩm Chính Hãng Store",
                alert_email="demo@ecomsight.vn",
                alert_enabled=False,  # Tắt email cho demo
                alert_threshold="high",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Tạo user demo: username=demo, password=demo1234")
        else:
            user = db.query(User).filter(User.username == "demo").first()
            print("ℹ️ User demo đã tồn tại")

        # Xóa reviews cũ của demo user
        existing = db.query(Review).filter(Review.user_id == user.id).count()
        if existing > 10:
            print(f"ℹ️ Đã có {existing} reviews, bỏ qua seed")
            return

        # Tạo reviews mẫu với timestamp ngẫu nhiên (30 ngày qua)
        all_sample = SAMPLE_REVIEWS + CRITICAL_REVIEWS
        created = 0

        for sentiment, platform, product, stars, comment, aspect in all_sample:
            # Random timestamp trong 30 ngày qua
            days_ago = random.randint(0, 29)
            hours_ago = random.randint(0, 23)
            ts = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)

            result = analyze_review(comment, use_phobert=False)  # Nhanh hơn khi seed

            review = Review(
                user_id=user.id,
                platform=platform,
                product_name=product,
                comment=comment,
                rating_star=stars,
                sentiment_label=sentiment,  # Dùng ground truth
                sentiment_score=round(random.uniform(0.75, 0.98), 3),
                sentiment_source="model",
                aspect_label=aspect,
                urgency_label=result["urgency_label"],
                analyzed_at=ts,
                created_at=ts,
                review_date=ts,
                author_username=f"user_{random.randint(1000, 9999)}",
                is_labeled=False,
            )
            db.add(review)
            created += 1

        # Thêm nhiều reviews ngẫu nhiên để có data đủ cho charts
        extra_positive = [
            "Dùng thấy da mịn màng và sáng hơn, sẽ mua lại ủng hộ shop!",
            "Hàng chính hãng, đóng gói đẹp, giao nhanh. Tuyệt vời!",
            "Kem dưỡng này xứng đáng 5 sao, giá hợp lý chất lượng tốt.",
            "Shop phục vụ nhiệt tình, hàng y hình, mình hài lòng lắm.",
            "Dùng 2 tuần thấy da cải thiện rõ ràng, không còn khô và sần sùi.",
        ]
        extra_negative = [
            "Giao hàng chậm, hộp bị móp, chất lượng không đúng mô tả.",
            "Sản phẩm không hiệu quả như quảng cáo, tiếc tiền đã mua.",
            "Shop không hỗ trợ đổi trả, thái độ phục vụ kém.",
        ]
        extra_neutral = [
            "Sản phẩm bình thường, không có gì đặc biệt.",
            "Tạm ổn thôi, chờ xem thêm vài tuần nữa.",
        ]

        products_extra = [
            ("CeraVe Moisturizing Cream", "shopee"),
            ("La Roche-Posay Toleriane", "shopee"),
            ("Cosrx Advanced Snail", "tiktok"),
            ("Paula's Choice BHA", "tiktok"),
            ("The Ordinary Hyaluronic", "shopee"),
        ]

        for _ in range(60):
            r_type = random.choices(["positive", "negative", "neutral"], weights=[60, 25, 15])[0]
            product, platform = random.choice(products_extra)
            days_ago = random.randint(0, 29)

            if r_type == "positive":
                comment = random.choice(extra_positive)
                stars = random.choice([4, 5])
                urgency = "low"
            elif r_type == "negative":
                comment = random.choice(extra_negative)
                stars = random.choice([1, 2])
                urgency = "medium"
            else:
                comment = random.choice(extra_neutral)
                stars = 3
                urgency = "low"

            ts = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))

            review = Review(
                user_id=user.id,
                platform=platform,
                product_name=product,
                comment=comment,
                rating_star=stars,
                sentiment_label=r_type,
                sentiment_score=round(random.uniform(0.70, 0.95), 3),
                sentiment_source="model",
                aspect_label=random.choice(["product", "shipping", "service", "price"]),
                urgency_label=urgency,
                analyzed_at=ts,
                created_at=ts,
                review_date=ts,
                is_labeled=False,
            )
            db.add(review)
            created += 1

        db.commit()
        print(f"✅ Đã tạo {created} reviews mẫu")

        # Tạo alerts mẫu
        alerts_data = [
            ("Phát hiện review nghi hàng giả", "Sản phẩm 'Kem trị mụn No-Brand' nhận review nghi ngờ hàng nhái", "critical"),
            ("Nhiều khách phàn nàn kích ứng", "2 review báo cáo kích ứng da trong 24h qua", "critical"),
            ("Review tiêu cực về vận chuyển", "Giao hàng chậm hơn 3 ngày so với cam kết", "high"),
            ("Điểm đánh giá giảm", "Điểm trung bình giảm từ 4.8 xuống 4.2 trong 7 ngày", "medium"),
        ]

        for title, msg, urgency in alerts_data:
            alert = Alert(
                user_id=user.id,
                title=title,
                message=msg,
                urgency=urgency,
                is_read=False,
                created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
            )
            db.add(alert)

        db.commit()
        print("✅ Đã tạo alerts mẫu")
        print("\n🎉 Seed database hoàn tất!")
        print("   Username: demo")
        print("   Password: demo1234")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
