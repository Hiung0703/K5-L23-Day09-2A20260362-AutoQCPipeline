# Báo cáo Day 09 — Hồ Xuân Hùng, MSHV 2A20260362

## 1. Kết luận trước
**Hold**, mã thoát **10**: nhận **205/224 ảnh**, loại 19; duyệt **80 ảnh**, còn **0 lỗi bắt buộc**, **38/205 ảnh cảnh báo chưa duyệt (18,54% ≥ 10%)**. Dataset xuất là bản nháp, chưa phát hành. Nguồn: [tóm tắt](reports/08_summary.json), [manifest](export/clean_v1/manifest.json).

## 2. Lỗi và phân việc
Số dưới đây là số issue trong [v1](reports/02_error_list_v1.csv), không phải số ảnh duy nhất; một ảnh/dòng có thể có nhiều lỗi.

| Mã lỗi | Số issue | Ai xử lý / cách xử lý |
|---|---:|---|
| CORRUPT_IMAGE / BAD_SIZE | 2 / 3 | Máy loại ảnh hỏng/quá nhỏ |
| DUP_IMAGE_EXACT / DUP_IMAGE_NEAR / LEAK_TEST | 8 / 2 / 4 | Máy loại ảnh trùng/rò rỉ |
| MISSING_LABEL_FILE / EMPTY_LABEL | 6 / 12 | Người gán/kiểm tra; máy không bịa nhãn |
| BAD_FORMAT / BAD_CLASS_ID / BOX_ZERO / DUP_BOX | 3 / 6 / 4 / 7 | Máy xoá dòng lỗi/lặp, ghi log |
| BOX_OUT_OF_IMAGE / BAD_CLASS_NAME | 8 / 2 | Máy cắt box / sửa tên lớp |
| BOX_HUGE / BOX_TINY / CLASS_RARE | 3 / 6 / 4 | Người kiểm; CLASS_RARE ở cấp dataset |
| POSSIBLE_MISSING / POSSIBLE_LOOSE_BOX | 53 / 28 | Người kiểm thiếu vật/box lỏng |
| POSSIBLE_WRONG_CLASS / POSSIBLE_FALSE_POS | 18 / 29 | Người kiểm nhầm lớp/box thừa |

[Log sửa](reports/03_fixes.csv) có 35 mục, gồm cả chuyển người gán. [Hàng đợi](reports/05_review_queue.csv) có 125 ảnh; đầu hàng `img_0020` có điểm **11,524** = 3×(1+0,9474) + 2×(1+0,8408) + 2, do nhầm lớp, thiếu box và lịch sử xoá dòng; cao hơn NEEDS_LABEL=10. Với 80 ảnh duyệt, bao phủ **94/123 cờ ngữ nghĩa** v2, trên **74/103 ảnh có cờ ngữ nghĩa** (đối chiếu [v2](reports/04_error_list_v2.csv) và [log duyệt](reports/06_review_log.csv)). Không gọi đây là số lỗi thật: raw không có đáp án.

## 3. Calibration (2 ngưỡng)
Nguồn: [sweep](calibration/calibration.json), [cấu hình chọn](calibration/selected/calibration.json); calib có 30 ảnh gốc + 9 ảnh trùng.

| Tham số | Trước → sau | Precision / Recall trước → sau | Đánh đổi |
|---|---|---|---|
| duplicates.phash_dist | 2 → **4** | NEAR: 1/0,500 → 1/0,667 | TP 3/6→4/6, FP=0; nhỏ nhất trong dải 4–14 có cùng điểm, tránh xoá nhầm |
| second_opinion.conf | 0,25 → **0,6** | WRONG_CLASS: 0,556/0,833→0,625/0,833; MISSING: 0,500/1→0,571/1 | Giữ TP 5/6 và 8/8, FP giảm 4→3 và 8→6 |

LOOSE_BOX giảm P/R **0,286/0,400→0,200/0,200** (TP 2/5→1/5): chấp nhận giảm khả năng phát hiện box lỏng để giảm báo động trong khi giữ recall thiếu box/nhầm lớp. Không chọn conf 0,7–0,8 vì recall thiếu box giảm còn 7/8–6/8. FALSE_POS không đổi **0,313/1** (TP=5, FP=11), do dùng fp_conf cố định. EXACT giữ P/R=1/1, TP=3/3.

**Bẫy calibration:** pHash=16 đạt NEAR P/R=1/0,833 nhưng gộp nhầm [img_0011](../data/raw/images/img_0011.jpg) (quần vợt) với [img_0008](../data/raw/images/img_0008.jpg) (trượt tuyết), khoảng cách 16; đã mở cả hai ảnh. Cờ duplicate/leak trên raw tăng 14→26 khi đổi 4→16. Calib không có LEAK_TEST; điểm NEAR tốt không bảo đảm intake an toàn. 5/6 ca nhầm lớp chèn là person→car, chưa đại diện cho car/truck/bus.

Đã mở các cặp raw `img_0042/0076` (cùng xe buýt 103 ROJA), `img_0037/0143` (cùng xe buýt/cần cẩu), `img_0012/0039` (cùng nhóm người ở bàn ăn). Hai cặp đầu khác kích thước, pHash=0; cặp cuối trùng byte. Loại các cặp này hợp lý, nhưng chỉ là kiểm tra mẫu. [Intake](reports/01_intake.csv) loại 19/224 ảnh, không đổi so với ngưỡng đầu.

## 4. Cửa chặn và điểm mù
Chạy `python -m pipeline.run --budget 0 --work work/run_nb --reports work/rep_nb --export-dir work/exp_nb`: **Rework, mã 20**, còn **6/205 ảnh thiếu file nhãn**, exported=null và không có dataset xuất. Giữ [bản sao báo cáo tự sinh](gate_budget0/08_summary.json), [lỗi v3](gate_budget0/07_error_list_v3.csv) để kiểm chứng.

Đã xem 10 ảnh raw (0001–0009, 0030): **0001** thiếu box người mặc quân phục, **0004** thiếu box xe góc phải dưới, **0006** có box người lặp. Xem lại sau pipeline: hai ca thiếu đã bổ sung, box lặp đã xoá (dòng 2 trong log sửa). Đây không phải ba điểm mù.

Hai điểm mù có bằng chứng trên calib: **gần trùng biến đổi mạnh** bỏ sót calib_037 và calib_038 (**2/6**); **box lỏng** bỏ sót calib_002, 006, 012, 024 (**4/5**). Đối chiếu [MANIFEST](../data/calib/MANIFEST.csv) với checker ở cấu hình chọn; không suy diễn các tỉ lệ này thành recall trên raw.

## 5. Train: raw vs clean
**Chưa chạy.** Train Colab là phần tùy chọn, chấm riêng; phiên này hoàn thiện phần lõi, chưa thực hiện thí nghiệm GPU. Không có số liệu mAP hoặc bằng chứng clean tốt hơn raw.

## 6. Quyết định và ghi chú AI
Giữ **Hold**, chỉ dùng bản nháp thử nghiệm. Release cần 0 lỗi bắt buộc và dưới 10% ảnh cảnh báo chưa duyệt: với 205 ảnh, tối đa 20. Hiện còn 38; cần xử lý ít nhất 18 ảnh nữa nếu mẫu số giữ nguyên, nhưng ngân sách lab 80 đã hết. Đề xuất vòng duyệt bổ sung được phê duyệt trong thực tế; không sửa ngân sách/gate hay làm checker mất recall để ép Release.

1. **Prompt:** triển khai 4 stub theo docstring/test; đầu vào YOLO, cấu hình, cache model; đầu ra Issue/verdict/log; check chỉ đọc, autofix chỉ sửa bản sao, WARN chuyển người, không bịa nhãn.
2. **Kiểm AI:** 79 test đề + [4 ca bổ sung](../scripts/test_step2_edges.py) xanh; thử hai lỗi/dòng, dòng trống, nhiều dự đoán, ID inf; đọc thao tác ghi/xoá, đo calib, xem ảnh trước/sau, thử gate budget 0.
3. **AI sai/thiếu:** thử commit trước khi kiểm tra danh tính Git, gặp Author identity unknown; đã hỏi tên/email thay vì tự gán. Test xanh không bảo đảm bắt hết lỗi thật.
