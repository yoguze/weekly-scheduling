let unsavedChanges = false;

window.onload = () => {
    generateTimeOptions();
    fetchCalendar();
    setupLeaveWarning();
};

function toggleForm() {
    const priority = parseInt(document.getElementById("priority").value);
    document.getElementById("flexibleForm").classList.add("hidden");
    document.getElementById("fixedForm").classList.add("hidden");

    if (priority >= 1 && priority <= 5) {
        document.getElementById("flexibleForm").classList.remove("hidden");
    } else if (priority === 6) {
        document.getElementById("fixedForm").classList.remove("hidden");
    }
}

function generateTimeOptions() {
    const startSelect = document.getElementById("startTime");
    const endSelect = document.getElementById("endTime");
    for (let h = 9; h <= 23; h++) {
        addOption(startSelect, h);
        addOption(endSelect, h);
    }
}

function addOption(selectElement, hour) {
    const option = document.createElement("option");
    option.value = hour;
    option.text = `${hour}:00`;
    selectElement.appendChild(option);
}

function submitForm() {
    const priority = parseInt(document.getElementById("priority").value);

    if (priority >= 1 && priority <= 5) {
        handleFlexible();
    } else if (priority === 6) {
        handleFixed();
    } else {
        setLog("優先度を選んでください。", "error");
    }
}

function handleFlexible() {
    const title = document.getElementById("title").value;
    const hours = document.getElementById("hours").value;
    const deadline = document.getElementById("deadline").value;

    if (!title || hours <= 0 || !deadline) {
        setLog("タイトル・期間・締切日をすべて入力してください。", "error");
        return;
    }

    fetch("/add_flexible", {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, hours, deadline })
    })
        .then(response => response.json())
        .then(data => {
            setLog(data.message, "success");
            fetchCalendar();
            unsavedChanges = false;
        });

    unsavedChanges = true;
}

function handleFixed() {
    const title = document.getElementById("taskTitle").value;
    const date = document.getElementById("fixedDate").value;
    const start = document.getElementById("startTime").value;
    const end = document.getElementById("endTime").value;

    if (!title || !date || start === "" || end === "") {
        setLog("タイトル・日付・開始・終了時刻を入力してください。", "error");
        return;
    }

    if (parseInt(start) >= parseInt(end)) {
        setLog("開始時刻は終了時刻よりも早くしてください。", "error");
        return;
    }

    fetch("/add_fixed", {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ taskTitle: title, fixedDate: date, startTime: start, endTime: end })
    })
        .then(response => response.json())
        .then(data => {
            setLog(data.message, "success");
            fetchCalendar();
            unsavedChanges = false;
        });

    unsavedChanges = true;
}

function setLog(message, type) {
    const logElement = document.getElementById("log");
    logElement.innerText = message;
    logElement.className = type;
}

function fetchCalendar() {
    fetch("/get_calendar")
        .then(response => response.text())
        .then(data => {
            document.getElementById("calendarView").innerHTML = data;
            setLog("カレンダー更新完了！", "success");
        });
}

function resetAllEvents() {
    if (confirm("全ての予定をリセットします。よろしいですか？")) {
        fetch("/reset_all", { method: "POST" })
            .then(() => {
                fetchCalendar();
                setLog("全予定をリセットしました！", "success");
            });
    }
}

function setupLeaveWarning() {
    window.addEventListener("beforeunload", function (e) {
        if (unsavedChanges) {
            e.preventDefault();
            e.returnValue = '';
        }
    });

    document.querySelectorAll("a, button").forEach(el => {
        el.addEventListener("click", function (e) {
            if (unsavedChanges) {
                if (!confirm("設定した予定は保存されません。別のページに移動しますか？")) {
                    e.preventDefault();
                }
            }
        });
    });
}

function downloadPDF() {
    window.location.href = "/download_pdf";
}
