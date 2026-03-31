def get_formats(workbook):
    formats = {}

    formats["bold_format"] = workbook.add_format({"bold": True, "font_size": 12})
    formats["center_bold_format"] = workbook.add_format(
        {"align": "center", "bold": True, "font_size": 11}
    )
    formats["week_header_format"] = workbook.add_format(
        {
            "align": "center",
            "bold": True,
            "font_size": 11,
            "bg_color": "#BDD7EE",
            "border": 1,
        }
    )
    formats["date_header_format"] = workbook.add_format(
        {"align": "center", "font_size": 10, "bg_color": "#FFF2CC", "border": 1}
    )
    formats["folder_name_format_1"] = workbook.add_format(
        {"bold": True, "bg_color": "#FF6A00", "border": 1, "font_color": "#000000"}
    )
    formats["folder_name_format_2"] = workbook.add_format(
        {"bold": True, "bg_color": "#FF6A00", "border": 1, "font_color": "#000000"}
    )
    formats["data_cell_format_1"] = workbook.add_format(
        {"border": 1, "bg_color": "#49CFDE"}
    )
    formats["data_cell_format_2"] = workbook.add_format(
        {"border": 1, "bg_color": "#49CFDE"}
    )

    formats["summary_header_format"] = workbook.add_format(
        {"bold": True, "bg_color": "#FFD966", "border": 1, "align": "center"}
    )
    formats["summary_cell_format"] = workbook.add_format(
        {"border": 1, "align": "center"}
    )
    formats["summary_negative_diff_format"] = workbook.add_format(
        {"border": 1, "align": "center", "font_color": "red"}
    )

    formats["red_left_border_format_week_sumary_row1"] = workbook.add_format(
        {
            "border": 1,
            "left": 2,
            "left_color": "red",
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#FFF2CC",
            "font_color": "#6B4226",
        }
    )

    formats["red_left_border_format_week_sumary_row2"] = workbook.add_format(
        {
            "border": 1,
            "left": 2,
            "left_color": "red",
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#C73C3E",
            "font_color": "#0A0A0A",
        }
    )

    formats["red_left_border_format_week_sumary_row3"] = workbook.add_format(
        {
            "border": 1,
            "left": 2,
            "left_color": "red",
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#D9EAD3",
            "font_color": "#38761D",
            "italic": True,
        }
    )

    formats["row_1_format"] = workbook.add_format(
        {
            "border": 1,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#FFF2CC",
            "font_color": "#6B4226",
            "bold": True,
        }
    )

    formats["row_2_format"] = workbook.add_format(
        {
            "border": 1,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#C73C3E",
            "font_color": "#0A0A0A",
        }
    )
    formats["row_3_format"] = workbook.add_format(
        {
            "border": 1,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#D9EAD3",
            "font_color": "#38761D",
            "italic": True,
        }
    )

    formats["red_left_border_format"] = workbook.add_format(
        {
            "border": 1,
            "left": 2,
            "left_color": "red",
            "bold": True,
            "align": "center",
            "valign": "vcenter",
        }
    )

    formats["red_left_border_date_format_days"] = workbook.add_format(
        {
            "align": "center",
            "font_size": 10,
            "bg_color": "#FFF2CC",
            "border": 1,
            "left": 2,
            "left_color": "red",
        }
    )

    formats["notes_format"] = workbook.add_format(
        {"bold": True, "bg_color": "#FFD966", "border": 1, "align": "center"}
    )

    formats["work"] = workbook.add_format(
        {"bold": True, "bg_color": "#FF6666", "border": 1, "align": "center"}
    )

    formats["remote"] = workbook.add_format(
        {"bold": True, "bg_color": "#CF66FF", "border": 1, "align": "center"}
    )

    formats["home"] = workbook.add_format(
        {"bold": True, "bg_color": "#66D1FF", "border": 1, "align": "center"}
    )

    formats["travel"] = workbook.add_format(
        {"bold": True, "bg_color": "#85E085", "border": 1, "align": "center"}
    )

    formats["folder_column_width"] = 20  # 👈 You can change this value as needed

    return formats
