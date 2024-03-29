#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import datetime as DT
import os.path

from app_web_server.app import app
from flask import render_template, send_from_directory

import config
from db import MetalRate
from root_common import MetalEnum


@app.route("/")
def index():
    items = []
    for metal_rate in MetalRate.get_last_rates(number=-1):
        items.append({
            "date": metal_rate.get_date_title(),
            "date_iso": metal_rate.date.isoformat(),
            "gold": float(metal_rate.gold),
            "silver": float(metal_rate.silver),
            "platinum": float(metal_rate.platinum),
            "palladium": float(metal_rate.palladium),
        })

    start_date, end_date = MetalRate.get_range_dates()
    filter_date = end_date - DT.timedelta(days=365)

    return render_template(
        "index.html",
        title="Цены драгоценных металлов",
        items=items,
        start_date=str(start_date),
        end_date=str(end_date),
        filter_date=str(filter_date),
        metals={
            metal.name_lower: {
                k: v for k, v in vars(metal).items() if not k.startswith("_")
            }
            for metal in MetalEnum
        },
    )


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static/images"),
        "favicon.png",
    )


if __name__ == "__main__":
    # app.debug = True

    app.run(
        host="0.0.0.0",
        port=config.PORT_WEB,
    )
