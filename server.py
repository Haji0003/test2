from fastapi import (
    FastAPI,
    HTTPException,
)  # FastAPIフレームワークの基本機能とエラー処理用のクラス
from fastapi.middleware.cors import CORSMiddleware  # CORSを有効にするためのミドルウェア
from fastapi.responses import HTMLResponse  # HTMLを返すためのレスポンスクラス
from pydantic import BaseModel  # データのバリデーション（検証）を行うための基本クラス
from typing import Optional  # 省略可能な項目を定義するために使用
import sqlite3  # SQLiteデータベースを使用するためのライブラリ
import uvicorn # ASGIサーバーを起動するためのライブラリ

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_db():
    with sqlite3.connect("training.db") as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS training (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_number INTEGER NOT NULL,
            day_of_week TEXT NOT NULL,
            training_content TEXT NOT NULL,
            sets INTEGER NOT NULL,
            completed BOOLEAN DEFAULT FALSE
        )
        """)


# 初期化
init_db()


class Training(BaseModel):
    week_number: int
    day_of_week: str
    training_content: str
    sets: int
    completed: Optional[bool] = False


class TrainingResponse(Training):
    id: int


# クライアント用のHTMLを返すエンドポイント
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("client.html", "r", encoding="utf-8") as f:
        return f.read()


# トレーニングメニューを追加するエンドポイント
@app.post("/trainings", response_model=TrainingResponse)
def add_training(training: Training):
    with sqlite3.connect("training.db") as conn:
        cursor = conn.execute("""
        INSERT INTO training (week_number, day_of_week, training_content, sets, completed)
        VALUES (?, ?, ?, ?, ?)
        """, (training.week_number, training.day_of_week, training.training_content, training.sets, training.completed))
        training_id = cursor.lastrowid
    return {**training.dict(), "id": training_id}


@app.get("/trainings")
def get_trainings():
    with sqlite3.connect("training.db") as conn:
        trainings = conn.execute("SELECT * FROM training").fetchall()
        return [{"id": t[0], "week_number": t[1], "day_of_week": t[2], "training_content": t[3], "sets": t[4], "completed": bool(t[5])} for t in trainings]


@app.put("/trainings/{training_id}")
def update_training(training_id: int, training: Training):
    with sqlite3.connect("training.db") as conn:
        cursor = conn.execute("""
        UPDATE training
        SET week_number = ?, day_of_week = ?, training_content = ?, sets = ?, completed = ?
        WHERE id = ?
        """, (training.week_number, training.day_of_week, training.training_content, training.sets, training.completed, training_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Training not found")
        return {**training.dict(), "id": training_id}


@app.delete("/trainings/{training_id}")
def delete_training(training_id: int):
    with sqlite3.connect("training.db") as conn:
        cursor = conn.execute(
            "DELETE FROM training WHERE id = ?", (training_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Training not found")
        return {"message": "Training deleted"}


@app.get("/trainings/{training_id}", response_model=TrainingResponse)
def get_training(training_id: int):
    with sqlite3.connect("training.db") as conn:
        training = conn.execute(
            "SELECT * FROM training WHERE id = ?", (training_id,)).fetchone()
        if training is None:
            raise HTTPException(status_code=404, detail="Training not found")
        return {
            "id": training[0],
            "week_number": training[1],
            "day_of_week": training[2],
            "training_content": training[3],
            "sets": training[4],
            "completed": bool(training[5])
        }


if __name__ == "__main__":
    # FastAPIアプリケーションを非同期モードで起動
    uvicorn.run(app, host="0.0.0.0", port=8000)
