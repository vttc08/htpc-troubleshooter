
console.log("test")

let errors = [{
    "code": "bluescreen",
    "message": '_("TV Blue Screen")', // jinja style
    "errimage": 'url_for("static", filename="images/blue_screen.png")',
    },
    {
    "code": "volume_too_low",
    "message": '_("Volume Too Low")', // jinja style
    "errimage": 'url_for("static", filename="images/volume_too_low.png")',
    },
    {
    "code": "just_player_error",
    "message": '_("Just Player Error")', // jinja style
    "errimage": 'url_for("static", filename="images/just_player_error.png")',
    },
    {
    "code": "buffering",
    "message": '_("Buffering")', // jinja style
    "errimage": 'url_for("static", filename="images/buffering.png")',
    },
    {
    "code": "audio_desync",
    "message": '_("Audio Desync")', // jinja style
    "errimage": 'url_for("static", filename="images/audio_desync.png")',
    },
    {
    "code": "no_zh_sub",
    "message": '_("No Chinese Subtitle")', // jinja style
    "errimage": 'url_for("static", filename="images/no_zh_sub.png")',
    },
    {
    "code": "sub_desync",
    "message": '_("Subtitle Desync")', // jinja style
    "errimage": 'url_for("static", filename="images/sub_desync.png")',
    }
]

document.addEventListener("DOMContentLoaded", function() {
    console.log("DOM fully loaded and parsed");
    let buttonContainer = document.querySelectorAll(".button-container")[0];
    // for (let i = 0; i < errors.length; i++) {
    //     let error = errors[i];
    //     console.log(error)
    //     let error_div = document.createElement("a");
    //     error_div.className = "err";
    //     error_div.href = "#";
    //     error_div.innerHTML = `{{${error["message"]}}}`;
    //     buttonContainer.appendChild(error_div);
    // }
});