# Ryan Turner (turnerry@iro.umontreal.ca)
from __future__ import division, print_function

import decimal
from builtins import range
from string import ascii_letters

import numpy as np
import pandas as pd
from scipy.special import expit as logistic

import benchmark_tools.sciprint as sp
from benchmark_tools.test_constants import MC_REPEATS_LARGE

ONE = decimal.Decimal("1")

# ============================================================================
# Decimal utils useful, but currently not used outside of test.
# ============================================================================


def decimal_left_digits(x_dec):
    assert sp.decimal_to_dot(x_dec)  # Should make exception
    y = 1 + max(0, x_dec.adjusted())
    return y


def decimal_right_digits(x_dec):
    assert sp.decimal_to_dot(x_dec)  # Should make exception
    x_tup = sp.as_tuple_chk(x_dec)
    y = max(0, -x_tup.exponent)
    return y


def decimal_digits(x_dec):
    assert sp.decimal_to_dot(x_dec)  # Should make exception
    x_tup = sp.as_tuple_chk(x_dec)
    y = len(x_tup.digits) - min(0, x_dec.adjusted())
    return y


def decimal_floor_log10_abs(x_dec):
    assert x_dec.is_finite() and x_dec != 0  # Should make exception
    return x_dec.adjusted()


def decimal_ceil_log10_abs(x_dec):
    k = decimal_floor_log10_abs(x_dec)
    assert abs(sp.decimal_1ek(k)) <= abs(x_dec)
    y = k + int(sp.decimal_1ek(k, signed=x_dec.is_signed()) != x_dec)
    return y


def decimal_next_pow10(x_dec):
    if x_dec == 0:
        return x_dec  # Note: this keeps sign and precision of original 0.
    k = decimal_ceil_log10_abs(x_dec)
    y = sp.decimal_1ek(k, signed=x_dec.is_signed())
    return y


# ============================================================================
# Now the tests
# ============================================================================


def decimal_eq(x, y):
    basic_eq = (x == y) or (x.is_nan() and y.is_nan())
    return basic_eq and (x.as_tuple() == y.as_tuple())


def decimal_shift(x_dec):
    """deprecated to adjusted."""
    x_tup = sp.as_tuple_chk(x_dec)
    return (len(x_tup.digits) + x_tup.exponent) - 1


def test_mod():
    x = np.random.randint(low=-20, high=20)
    mod = np.random.randint(low=1, high=20)

    y = sp.floor_mod(x, mod)
    assert y <= x and y % mod == 0 and y + mod > x

    y = sp.ceil_mod(x, mod)
    assert y >= x and y % mod == 0 and y - mod < x


def test_decimal_1ek():
    sign = np.random.rand() <= 0.5
    expo = np.random.randint(-12, 12)
    x = sp.decimal_1ek(expo, sign)
    y = -ONE.scaleb(expo) if sign else ONE.scaleb(expo)
    assert decimal_eq(x, y)


def test_decimal_shift():
    x = dec_rnd(all_finite=True)
    shift = decimal_shift(x)

    assert shift == x.adjusted()  # We should really just use adjusted

    # If x == 0, it is evaluated as if the last digit where a 1.
    if x.is_zero():
        x_tup = sp.as_tuple_chk(x)
        x = sp.decimal_1ek(x_tup.exponent, x_tup.sign)

    x_shifted = sp.decimal_1ek(-shift, signed=x.is_signed()) * x
    assert 1 <= x_shifted and x_shifted < 10
    assert decimal_floor_log10_abs(x_shifted) == 0
    assert decimal_left_digits(x_shifted) == 1


def test_decimal_left_digits():
    x = dec_rnd(to_dot=True, all_finite=True)
    str_x = str(abs(x))
    left_dig = len(str_x.split(".")[0])
    assert left_dig == decimal_left_digits(x)


def test_decimal_right_digits():
    x = dec_rnd(to_dot=True, all_finite=True)
    str_x = str(x)
    L = str_x.split(".")
    right_dig = 0 if len(L) <= 1 else len(L[1])
    assert right_dig == decimal_right_digits(x)


def test_decimal_digits():
    x = dec_rnd(to_dot=True, all_finite=True)
    str_x = str(abs(x))
    dig = sum(len(ss) for ss in str_x.split("."))
    assert dig == decimal_digits(x)


def test_decimal_floor_log10():
    x = dec_rnd(no_zero=True, all_finite=True)
    y = int(np.floor(float(abs(x).log10())))
    assert y == decimal_floor_log10_abs(x)


def test_decimal_ceil_log10():
    x = dec_rnd(no_zero=True, all_finite=True)
    y = int(np.ceil(float(abs(x).log10())))
    assert y == decimal_ceil_log10_abs(x)


def test_decimal_next_pow10():
    x = dec_rnd(all_finite=True)
    y = decimal_next_pow10(x)
    assert x.is_signed() == y.is_signed()
    assert abs(x) <= abs(y)
    if x == 0:
        assert decimal_eq(x, y)
    else:
        assert decimal_ceil_log10_abs(x) == decimal_ceil_log10_abs(y)


def test_decimal_to_dot():
    x = dec_rnd()
    to_dot = ("E" not in str(x)) and x.is_finite()
    assert to_dot == sp.decimal_to_dot(x)


def test_create_decimal():
    x = np.random.randn() * np.exp(np.random.randn())
    digits = np.random.randint(low=1, high=10)
    x_dec = sp.create_decimal(x, digits)
    # Note: this will not always hold if x == 0
    assert len(x_dec.as_tuple().digits) == digits


def test_digit_str():
    x = dec_rnd(all_finite=True)
    expo = x.as_tuple().exponent
    str_x = sp.digit_str(x)
    str_x_2 = str(abs(x).scaleb(-expo))
    assert str_x == str_x_2


def test_print_estimate():
    mu = dec_rnd()
    EB = dec_rnd(all_pos=True)
    if mu.is_finite() and EB.is_finite():
        mu = mu.quantize(EB, rounding=decimal.ROUND_HALF_UP)

    shift = np.random.randint(low=-6, high=6)
    rev_shift = sp.decimal_1ek(-shift)

    clips = dec_rnd_list(2, all_finite=True)
    min_clip = min(clips)
    max_clip = max(clips)

    if np.random.rand() <= 0.5 or min_clip == max_clip:
        min_clip = sp.D_NINF
    if np.random.rand() <= 0.5:
        max_clip = sp.D_INF

    try:
        str_x = sp.print_estimate(mu, EB, shift, min_clip, max_clip)
    except ValueError:
        # Check we gave it a bad shift
        min_shift, max_shift, all_small = sp.get_shift_range([mu], shift_mod=1)
        assert all_small or shift < min_shift or shift > max_shift
        return

    if mu.is_nan():
        assert str_x == "nan"
    elif max_clip < mu:
        x_d = decimal.Decimal(str_x[1:].replace(",", ""))
        # Don't require the same number of digits of prec in the event of clip
        assert x_d * rev_shift == max_clip
    elif mu < min_clip:
        x_d = decimal.Decimal(str_x[1:].replace(",", ""))
        assert x_d * rev_shift == min_clip
    elif mu == sp.D_INF:
        assert str_x == "inf"
    elif mu == sp.D_NINF:
        assert str_x == "-inf"
    elif not EB.is_finite():
        mu2 = decimal.Decimal(str_x.replace(",", ""))
        assert decimal_eq(mu, mu2 * rev_shift)
    else:
        mu2 = decimal.Decimal(str_x.split("(")[0].replace(",", ""))
        assert decimal_eq(mu, mu2 * rev_shift)

        EB_mantissa = tuple(int(cc) for cc in str_x.split("(")[1][:-1])
        EB_expo = mu2.as_tuple().exponent
        EB2 = decimal.Decimal(decimal.DecimalTuple(0, EB_mantissa, EB_expo))
        assert decimal_eq(EB, EB2 * rev_shift)


def valid_list(x_dec_list, shift, all_small=False):
    sft = sp.decimal_1ek(shift)
    min_req = any((x_dec * sft).adjusted() >= 0 for x_dec in x_dec_list)
    max_req = all(sp.decimal_to_dot(x_dec * sft) for x_dec in x_dec_list)
    valid = max_req and (all_small or min_req)
    return valid


def test_get_shift_range():
    N = np.random.randint(low=1, high=6)
    x_dec_list = dec_rnd_list(N, all_finite=True)
    shift_mod = np.random.randint(low=1, high=6)

    min_shift, max_shift, all_small = sp.get_shift_range(x_dec_list, shift_mod)
    assert min_shift % shift_mod == 0
    assert max_shift % shift_mod == 0

    # min side test is supposed to fail sometimes by all_small condition
    assert not valid_list(x_dec_list, min_shift - shift_mod, all_small=False)
    assert not valid_list(x_dec_list, max_shift + shift_mod, all_small)

    for shift in range(min_shift, max_shift + 1):
        if shift % shift_mod == 0:
            assert valid_list(x_dec_list, shift, all_small)


def quantize_def(x, err):
    """Helper for test_find_shift()."""
    y = x.quantize(err, rounding=decimal.ROUND_HALF_UP) if x.is_finite() and err.is_finite() else x
    return y


def test_find_shift():
    N = np.random.randint(low=1, high=6)
    shift_mod = np.random.randint(low=1, high=6)

    mu = dec_rnd_list(N, all_finite=True)
    EB = dec_rnd_list(N, all_pos=True)
    mu = [quantize_def(x, err) for x, err in zip(mu, EB)]

    min_shift, max_shift, _ = sp.get_shift_range(mu, shift_mod)

    best_shift = sp.find_shift(mu, EB, shift_mod)
    assert min_shift <= best_shift and best_shift <= max_shift
    assert best_shift % shift_mod == 0

    max_len_0 = max(sp.str_print_len(sp.print_estimate(mm, ee, best_shift)) for mm, ee in zip(mu, EB))

    for shift in range(min_shift, max_shift + 1):
        if shift % shift_mod != 0:
            continue

        max_len = max(sp.str_print_len(sp.print_estimate(mm, ee, shift)) for mm, ee in zip(mu, EB))
        if abs(best_shift) <= abs(shift):
            assert max_len_0 <= max_len
        else:
            assert max_len_0 < max_len


def test_format_table():
    N = np.random.randint(low=1, high=6)
    M = np.random.randint(low=1, high=6)
    # Keeping it sorted makes it easier to compare before and after
    methods = sorted(np.random.choice(list(ascii_letters), N, replace=False))
    metrics = sorted(np.random.choice(list(ascii_letters), M, replace=False))

    shift_mod = np.random.randint(low=0, high=6)
    shift_mod = None if shift_mod == 0 else shift_mod
    to_dot = shift_mod is None

    stats = (sp.MEAN_COL, sp.ERR_COL, sp.PVAL_COL)
    cols = pd.MultiIndex.from_product([metrics, stats], names=["metric", "stat"])
    perf_tbl_dec = pd.DataFrame(index=methods, columns=cols, dtype=object)
    perf_tbl_dec.index.set_names("method", inplace=True)
    print("name", perf_tbl_dec.index.name)

    crap_limit_max = {}
    crap_limit_min = {}
    for metric in metrics:
        mu = dec_rnd_list(N, to_dot=to_dot, all_finite=True)
        EB = dec_rnd_list(N, to_dot=to_dot, all_pos=True)
        mu = [quantize_def(x, err) for x, err in zip(mu, EB)]

        min_clip = np.random.randint(-6, 6)
        max_clip = np.random.randint(-6, 6)

        if np.random.rand() <= 0.5:
            crap_limit_min[metric] = min_clip
        if np.random.rand() <= 0.5:
            crap_limit_max[metric] = max_clip

        pval_prec = np.random.randint(low=1, high=6)
        pval = [decimal.Decimal(np.random.rand()) for _ in range(N)]
        pval = [p.quantize(sp.decimal_1ek(-pval_prec), rounding=decimal.ROUND_CEILING) for p in pval]
        # Doesn't do snan but prob good enough
        pval = [decimal.Decimal("nan") if np.random.rand() <= 0.1 else p for p in pval]

        perf_tbl_dec.loc[:, (metric, sp.MEAN_COL)] = mu
        perf_tbl_dec.loc[:, (metric, sp.ERR_COL)] = EB
        perf_tbl_dec.loc[:, (metric, sp.PVAL_COL)] = pval

    pad = True
    perf_tbl_str, shifts = sp.format_table(perf_tbl_dec, shift_mod, pad, crap_limit_max, crap_limit_min)
    assert perf_tbl_str.index.name == "method"
    for metric in metrics:
        min_clip = sp.decimal_1ek(crap_limit_min.get(metric, "F"), signed=True)
        max_clip = sp.decimal_1ek(crap_limit_max.get(metric, "F"))
        rev_shift = sp.decimal_1ek(-shifts[metric])
        for method in methods:
            # Use strip to undo the padding
            str_x = perf_tbl_str.loc[method, (metric, sp.EST_COL)].strip(" ")
            assert "E" not in str_x
            str_p = perf_tbl_str.loc[method, (metric, sp.PVAL_COL)]
            assert "E" not in str_p
            # remove < for when at minimum quantum
            str_p = str_p.lstrip("<")

            mu = perf_tbl_dec.loc[method, (metric, sp.MEAN_COL)]
            EB = perf_tbl_dec.loc[method, (metric, sp.ERR_COL)]
            pval = perf_tbl_dec.loc[method, (metric, sp.PVAL_COL)]

            assert decimal_eq(decimal.Decimal(str_p), pval)

            if mu.is_nan():
                assert str_x == "nan"
            elif max_clip < mu:
                d_x = decimal.Decimal(str_x[1:].replace(",", ""))
                # Don't require the same # of digits of prec for a clip
                assert d_x * rev_shift == max_clip
            elif mu < min_clip:
                d_x = decimal.Decimal(str_x[1:].replace(",", ""))
                assert d_x * rev_shift == min_clip
            elif mu == sp.D_INF:
                assert str_x == "inf"
            elif mu == sp.D_NINF:
                assert str_x == "-inf"
            elif not EB.is_finite():
                mu2 = decimal.Decimal(str_x.replace(",", ""))
                assert decimal_eq(mu, mu2 * rev_shift)
            else:
                mu2 = decimal.Decimal(str_x.split("(")[0].replace(",", ""))
                assert decimal_eq(mu, mu2 * rev_shift)

                EB_mantissa = tuple(int(cc) for cc in str_x.split("(")[1][:-1])
                EB_expo = mu2.as_tuple().exponent
                EB2 = sp.decimal_from_tuple(0, EB_mantissa, EB_expo)
                assert decimal_eq(EB, EB2 * rev_shift)


def test_decimalize():
    N = np.random.randint(low=1, high=3)
    M = np.random.randint(low=1, high=3)
    # Keeping it sorted makes it easier to compare before and after
    methods = sorted(np.random.choice(list(ascii_letters), N, replace=False))
    metrics = sorted(np.random.choice(list(ascii_letters), M, replace=False))

    stats = (sp.MEAN_COL, sp.ERR_COL, sp.PVAL_COL)
    cols = pd.MultiIndex.from_product([metrics, stats], names=["metric", "stat"])
    perf_tbl = pd.DataFrame(index=methods, columns=cols, dtype=object)
    perf_tbl.index.set_names("method", inplace=True)
    crap_limit_max = {}
    crap_limit_min = {}
    for metric in metrics:
        mu = fp_rnd_list(N, all_finite=True)
        EB = np.abs(fp_rnd_list(N))
        pval = logistic(fp_rnd_list(N))

        perf_tbl.loc[:, (metric, sp.MEAN_COL)] = mu
        perf_tbl.loc[:, (metric, sp.ERR_COL)] = EB
        perf_tbl.loc[:, (metric, sp.PVAL_COL)] = pval

        min_clip = np.random.randint(-6, 6)
        max_clip = np.random.randint(-6, 6)

        if np.random.rand() <= 0.5:
            crap_limit_min[metric] = min_clip
        if np.random.rand() <= 0.5:
            crap_limit_max[metric] = max_clip

    print(perf_tbl)
    err_digits = np.random.randint(low=1, high=6)
    pval_digits = np.random.randint(low=1, high=6)
    default_digits = np.random.randint(low=1, high=6)
    perf_tbl_dec = sp.decimalize(perf_tbl, err_digits, pval_digits, default_digits)
    print(perf_tbl_dec)

    assert (
        not (perf_tbl_dec.xs(sp.PVAL_COL, axis=1, level=sp.STAT) < perf_tbl.xs(sp.PVAL_COL, axis=1, level=sp.STAT))
        .any()
        .any()
    )
    assert (
        not (perf_tbl_dec.xs(sp.ERR_COL, axis=1, level=sp.STAT) < perf_tbl.xs(sp.ERR_COL, axis=1, level=sp.STAT))
        .any()
        .any()
    )

    shift_mod = np.random.randint(low=0, high=6)
    # If there are some not to dot numbers we can't use shift_mod=None for no
    # shifting.
    if shift_mod == 0:
        mean_els = perf_tbl_dec.xs("mean", axis=1, level="stat").values.ravel()
        all_to_dot = all(sp.decimal_to_dot(mm) for mm in mean_els)
        shift_mod = None if all_to_dot else 1

    pad = True
    perf_tbl_str, shifts = sp.format_table(perf_tbl_dec, shift_mod, pad, crap_limit_max, crap_limit_min)
    print(perf_tbl_str)
    print("-" * 10)


DEC_TESTS = [
    test_mod,
    test_decimal_1ek,
    test_decimal_shift,
    test_decimal_left_digits,
    test_decimal_right_digits,
    test_decimal_digits,
    test_decimal_floor_log10,
    test_decimal_ceil_log10,
    test_decimal_next_pow10,
    test_decimal_to_dot,
    test_create_decimal,
    test_digit_str,
    test_print_estimate,
    test_get_shift_range,
    test_find_shift,
]


def fp_rnd_list(N, all_finite=False):
    x = np.exp(np.random.randn(N)) * np.random.randn(N)
    if not all_finite:
        idx = np.random.rand(N) <= 0.05
        x[idx] = np.random.choice([np.nan, -np.inf, np.inf], size=np.sum(idx), replace=True)
    return x


def dec_rnd(to_dot=False, no_zero=False, all_pos=False, all_finite=False):
    sign = 0 if all_pos else int(np.random.rand() <= 0.5)

    mantissa = np.random.randint(low=0, high=10, size=np.random.randint(12))
    if no_zero:
        mantissa = np.concatenate((mantissa, np.random.randint(low=1, high=10, size=1)))

    # Give decimal package exactly typed data, but only sometimes to check
    # type flexibility
    if np.random.rand() <= 0.5:
        mantissa = tuple([int(mm) for mm in mantissa])

    upper = 0 if to_dot else 6
    expo = np.random.randint(-6, upper)

    if (not all_finite) and np.random.rand() <= 0.1:
        expo = np.random.choice(["F", "n", "N"])

    x = sp.decimal_from_tuple(sign, mantissa, expo)
    return x


def dec_rnd_list(N, to_dot=False, all_pos=False, all_finite=False):
    return [dec_rnd(to_dot=to_dot, all_pos=all_pos, all_finite=all_finite) for _ in range(N)]


if __name__ == "__main__":
    np.random.seed(8235)

    for rr in range(MC_REPEATS_LARGE):
        test_decimalize()
    print("test_decimalize done")

    for rr in range(MC_REPEATS_LARGE):
        test_format_table()
    print("test_format_table done")

    for rr in range(MC_REPEATS_LARGE):
        for f in DEC_TESTS:
            f()
    print("passed")
