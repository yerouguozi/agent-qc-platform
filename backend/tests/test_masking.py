from app.gateway.masking import mask_arguments, mask_text


def test_phone_masked():
    assert mask_text("电话 13812345678 联系") == "电话 138****5678 联系"


def test_long_digits_masked():
    assert mask_text("金额 1234567890 元") == "金额 12****90 元"


def test_dict_nested():
    out = mask_arguments({"sql": "select * from t where phone='13900001111'", "limit": 10})
    assert "13900001111" not in out["sql"]
    assert out["limit"] == 10