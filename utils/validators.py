def positive_int(v):
    try:
        x=int(v)
        return x if x>=0 else None
    except (TypeError,ValueError): return None
