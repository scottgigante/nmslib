import warnings

DENSE_SPACES = [
    "lp",
    "l1",
    "l2",
    "linf",
    "l2sqr_sift",
    "cosinesimil",
    "negdotprod",
    "angulardist",
    "kldivfast",
    "kldivfastrq",
    "kldivgenslow",
    "kldivgenfast",
    "kldivgenfastrq",
    "itakurasaitoslow",
    "itakurasaitofast",
    "itakurasaitofastrq",
    "jsdivslow",
    "jsdivfast",
    "jsdivfastapprox",
    "jsmetrslow",
    "jsmetrfast",
    "jsmetrfastapprox",
    "renyidiv_slow",
    "renyidiv_fast",
    "leven",
    "normleven",
    "bit_jaccard",
    "bit_hamming",
]

SPARSE_SPACES = [
    "lp_sparse",
    "l1_sparse",
    "l2_sparse",
    "linf_sparse",
    "cosinesimil_sparse",
    "cosinesimil_sparse_fast",
    "negdotprod_sparse",
    "negdotprod_sparse_fast",
    "angulardist_sparse",
    "angulardist_sparse_fast",
    "jaccard_sparse",
]

VALID_SPACES = DENSE_SPACES + SPARSE_SPACES

PARAMETERIZED_SPACES = {"lp": "p", "renyidiv_slow": "alpha", "renyidiv_fast": "alpha"}

DENSE_TO_SPARSE = {
    "lp": "lp_sparse",
    "l1": "l1_sparse",
    "l2": "l2_sparse",
    "linf": "linf_sparse",
    "cosinesimil": "cosinesimil_sparse",
    "negdotprod": "negdotprod_sparse",
    "angular": "angular_sparse",
    "bit_jaccard": "jaccard_sparse",
}

SPARSE_TO_DENSE = {
    "lp_sparse": "lp",
    "l1_sparse": "l1",
    "l2_sparse": "l2",
    "linf_sparse": "linf",
    "cosinesimil_sparse": "cosinesimil",
    "cosinesimil_sparse_fast": "cosinesimil",
    "negdotprod_sparse": "negdotprod",
    "negdotprod_sparse_fast": "negdotprod",
    "angular_sparse": "angular",
    "angular_sparse_fast": "angular",
    "jaccard_sparse": "jaccard",
}


def _parse_parameterized_space(space):
    space_split = space.split(":")
    if len(space_split) == 1:
        return space, None, None
    elif len(space_split) > 2:
        raise ValueError(
            "Expected a maximum of 1 colon in space name. " "Got {}".format(space)
        )
    param = space_split[1]
    if not len(space_split[1].split("=")) == 2:
        raise ValueError(
            "Expected parameterized space to have format name:param=value. "
            "Got {}".format(space)
        )
    param, value = space_split[1].split("=")
    value = float(value)
    space = space_split[0]
    if space not in PARAMETERIZED_SPACES:
        raise ValueError("{} is not a parameterized space.")
    param_expected = PARAMETERIZED_SPACES[space]
    if param != param_expected:
        raise ValueError(
            "Expected parameter {} with {} space. "
            "Got {}".format(param_expected, space, param)
        )
    return space, param, value


def valid_space(space, data_type=None):
    space, _, _ = _parse_parameterized_space(space)
    if not space in VALID_SPACES:
        raise ValueError(
            "{} is not a valid space. " "Choose from {}".format(space, VALID_SPACES)
        )
    return True


def sparse_space(space, coerce=True):
    space_name, param, value = _parse_parameterized_space(space)
    if space_name in SPARSE_SPACES:
        return space
    elif space_name in DENSE_TO_SPARSE and coerce is True:
        new_space_name = DENSE_TO_SPARSE[space_name]
        fast_space_name = "{}_fast".format(new_space_name)
        if fast_space_name in SPARSE_SPACES:
            warnings.warn(
                "Converted {} to {}. "
                "For fast version, specify {} explicitly".format(
                    space_name, new_space_name, fast_space_name
                )
            )
        if param is not None:
            return "{}:{}={}".format(new_space_name, param, value)
        else:
            return new_space_name
    else:
        raise ValueError(
            "{} is not a valid space for sparse data. "
            "Choose from {}".format(space, SPARSE_SPACES)
        )


def dense_space(space, coerce=True):
    space_name, param, value = _parse_parameterized_space(space)
    if space_name in DENSE_SPACES:
        return space
    elif space_name in SPARSE_TO_DENSE and coerce is True:
        new_space_name = SPARSE_TO_DENSE[space_name]
        fast_space_name = "{}_fast".format(new_space_name)
        if fast_space_name in DENSE_SPACES:
            warnings.warn(
                "Converted {} to {}. "
                "For fast version, specify {} explicitly".format(
                    space_name, new_space_name, fast_space_name
                )
            )
        if param is not None:
            return "{}:{}={}".format(new_space_name, param, value)
        else:
            return new_space_name
    else:
        raise ValueError(
            "{} is not a valid space for dense data. "
            "Choose from {}".format(space, DENSE_SPACES)
        )
