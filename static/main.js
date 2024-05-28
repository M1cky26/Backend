document.addEventListener('DOMContentLoaded', function () {
});

function register() {
    let username = $('#username').val();
    if (!username) {
        return alert('Please enter your username');
    }
    let password = $('#password').val(); // Mengambil nilai dari input password
    if (!password) {
        return alert('Please enter your password');
    }

    let password2 = $('#password2').val(); // Mengambil nilai dari input konfirmasi password
    if (!password2) {
        return alert('Please enter your password confirmation');
    }

    if (password !== password2) {
        return alert('Password and password confirmation do not match');
    }

    console.log(username, password);
    $.ajax({
        type: "POST",
        url: "/register",
        data: {
            username: username,
            password: password,
        },
        success: function (response) {
            if (response['result'] === 'success') {
                alert("Registration complete!");
                window.location.href = "/login";
            } else {
                alert(response['msg']);
            }
        },
    });
}

function createevent() {
    let image = $('#fileInput').val();
    let title = $('#title').val();
    let desc = $('#desc').val();
    let locate = $('#locate').val();
    let date = $('#date').val();
    if (!title) {
        return alert('Please enter title');
    }
    if (!image) {
        return alert('Please enter banner image');
    }
    if (!desc) {
        return alert('Please enter description');
    }
    if (!locate) {
        return alert('Please enter locate');
    }
    if (!date) {
        return alert('Please enter date');
    }
    form_data.append("image_give", image);
    form_data.append("title_give", title);
    form_data.append("desc_give", desc);
    form_data.append("locate_give", locate);
    form_data.append("date_give", date);
    $.ajax({
        type: "POST",
        url: "/admin/event",
        data: form_data,
        contentType: false,
        processData: false,
        success: function (response) {
            alert(response["msg"]);
            window.location.reload();
        },
        error: function (xhr, status, error) {
            console.error("AJAX request error:", status, error);
        }
    });
}

function eventcard() {
    $.ajax({
        type: "GET",
        url: "/admin/event",
        success: function (response) {
            let events = response["events"];
            for (let i = 0; i < events.length; i++) {
                let image = events[i]["image"];
                let title = events[i]["title"];
                let desc = events[i]["desc"];
                let locate = events[i]["locate"];
                let date = events[i]["date"];

                let temp_html = `
                <div class="container">
                    <a class="desc" href="/"><i class="bi bi-arrow-left"></i>back
                    </a>
                    <div class="col flex-col ">
                        <div class="card card-event mb-3">
                            <img src="${image}" class="object-fit-xxl-contain border rounded"
                                alt="...">
                            <div class="card-body-event">
                                <h5 class="subtitle">${title}</h5>
                                <p class="desc" id="desc-event" style="color: gray;">${desc}</p>
                                <p class="desc" id="date-event " >${date}
                                </p>
                                <p class="desc" id="location-event">${locate}
                                </p>
                            </div>
                        </div>
                    </div>
                </div> `;

                $("#createevent").append(temp_html);
            }
        },
        error: function (xhr, status, error) {
            console.error("AJAX request error:", status, error);
        }
    });
}


// FUNGSI UPDATE ATAU EDIT PROFILE

function update() {
    let name = $("#username").val();
    let file = $("#input-pic")[0].files[0];
    let bio = $("#input-bio").val();
    let form_data = new FormData();
    
    form_data.append("file_give", file);
    form_data.append("name_give", name);
    form_data.append("about_give", bio);
    
    console.log(name, file, bio, form_data);

    $.ajax({
        type: "POST",
        url: "/profile/update",
        data: form_data,
        cache: false,
        contentType: false,
        processData: false,
        success: function (response) {
            if (response["result"] === "success") {
                alert(response["msg"]);
                window.location.reload();
            }
        },
    });
}
