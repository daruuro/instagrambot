def escape_chars(str_obj):
    str_obj = str_obj.replace("#", "\#")
    str_obj = str_obj.replace("\n", "\n>")
    return str_obj
