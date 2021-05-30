import requests
from app.core.console.log_collector import ConsoleLogCollector
from datetime import datetime, timedelta
from typing import Any, Callable, TypedDict

import celery
import time
import os.path
from uuid import UUID

from sqlalchemy.sql import schema
from app import models, schemas, crud
from app.core import console
from app.api import deps
from app.celery import celery as celery_app
from sqlalchemy.orm import Session
from app.db.session import DatabaseSession, session_manager


# NOTE I love my spaghetti code
@celery_app.task(bind=True)
def plot_queue_task(
    self: celery.Task,
    *,
    session_factory: Callable[[], Session] = DatabaseSession,
) -> Any:
    with session_manager(session_factory) as db:
        plot_queue_ids = [
            plot_queue.id for plot_queue in crud.plot_queue.get_multi(db)[1]
        ]
    log_collector = ConsoleLogCollector()

    for plot_queue_id in plot_queue_ids:
        with session_manager(session_factory) as db:
            plot_queue = crud.plot_queue.get(db, id=plot_queue_id)

            if plot_queue is None:
                raise RuntimeError(
                    f"Can not find a plot queue with id {plot_queue_id} in a database"
                )

            server_data = schemas.ServerReturn.from_orm(plot_queue.server)
            final_dir = plot_queue.final_dir.location
            final_dir_sub = os.path.join(final_dir, f"{plot_queue.id}")
            temp_dir = plot_queue.temp_dir.location
            temp_dir_sub = os.path.join(temp_dir, f"{plot_queue.id}")
            pool_key = plot_queue.server.pool_key
            farmer_key = plot_queue.server.farmer_key
            plots_amount = plot_queue.plots_amount

            execution_id = plot_queue.execution_id
            autoplot = plot_queue.autoplot
            plotting_started = plot_queue.plotting_started
            host = server_data.hostname.split(":")[0]
            worker_password = plot_queue.server.worker_password
            worker_port = plot_queue.server.worker_port
            plotting_data = schemas.PlottingData(
                final_dir=final_dir_sub,
                temp_dir=temp_dir_sub,
                pool_key=pool_key,
                farmer_key=farmer_key,
                plots_amount=plots_amount,
                k=32,
                threads=2,
                ram=4608,
            )

        login_responce = requests.post(
            f"http://{host}:{worker_port}/login/access-token/",
            data={"username": "admin", "password": worker_password},
        )

        if not login_responce.ok:
            continue

        token_data = schemas.Token(**login_responce.json())
        auth_headers = {"Authorization": f"Bearer {token_data.access_token}"}

        if execution_id is None:
            if autoplot or plotting_started is None:
                responce = requests.post(
                    f"http://{host}/plotting/",
                    headers=auth_headers,
                    json=plotting_data.dict(),
                )
                with session_manager(session_factory) as db:
                    plot_queue = crud.plot_queue.get(db, id=plot_queue_id)
                    if responce.ok:
                        crud.plot_queue.update(
                            db,
                            db_obj=plot_queue,
                            obj_in={"status": schemas.PlotQueueStatus.FAILED.value},
                        )
                    else:
                        plotting_return = schemas.PlottingReturn(**responce.json())
                        plot_queue = crud.plot_queue.update(
                            db,
                            db_obj=plot_queue,
                            obj_in={
                                "status": schemas.PlotQueueStatus.PLOTTING.value,
                                "plotting_started": datetime.utcnow(),
                                "execution_id": plotting_return.id,
                            },
                        )
        else:
            responce = requests.get(
                f"http://{host}/plotting/{execution_id}/", headers=auth_headers
            )
            with session_manager(session_factory) as db:
                plot_queue = crud.plot_queue.get(db, id=plot_queue_id)
                if not responce.ok:
                    crud.plot_queue.update(
                        db,
                        db_obj=plot_queue,
                        obj_in={"status": schemas.PlotQueueStatus.FAILED.value},
                    )
                else:
                    plotting_data = schemas.PlottingReturn(**responce.json())
                    if plotting_data.finished:
                        if plotting_data.status_code == 0:
                            crud.plot_queue.update(
                                db,
                                db_obj=plot_queue,
                                obj_in={
                                    "status": schemas.PlotQueueStatus.WAITING.value
                                    if autoplot
                                    else schemas.PlotQueueStatus.PAUSED.value,
                                    "execution_id": None,
                                },
                            )
                        else:
                            crud.plot_queue.update(
                                db,
                                db_obj=plot_queue,
                                obj_in={"status": schemas.PlotQueueStatus.FAILED.value},
                            )
                    else:
                        plot_queue = crud.plot_queue.update(
                            db,
                            db_obj=plot_queue,
                            obj_in={"status": schemas.PlotQueueStatus.PLOTTING.value},
                        )

    return {"info": "done", "console": log_collector.get()}
