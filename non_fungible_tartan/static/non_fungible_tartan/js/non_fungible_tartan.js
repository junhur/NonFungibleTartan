"use strict"
const IMAGE_FIX_HEIGHT = 300;

function changeColor(elementId) {
    let cell = document.getElementById(elementId);
    let colorPicker = document.getElementById('id-color-picker');
    if (cell.style.backgroundColor !== 'white') {
        cell.style.backgroundColor = 'white';
    } else {
        cell.style.backgroundColor = colorPicker.value;
    }

}

function makeCells() {
    let palette = document.getElementById('id-create-palette');
    let t = document.createElement("table");
    t.id = 'id-create-nft-table';
    for (let rows = 0; rows < 13; rows++) {
        let newRow = document.createElement("tr");
        newRow.id = 'create-palette-tr-' + rows;
        newRow.className = 'create-palette-tr';
        for (let cols = 0; cols < 13; cols++) {
            let newCell = document.createElement("td");
            newCell.id = 'create-palette-td-' + (rows * 13 + cols);
            newCell.className = 'create-palette-td';
            let newCellButton = document.createElement("button");
            newCellButton.id = 'create-palette-button' + (rows* 13 + cols);
            newCellButton.type = 'button';
            newCellButton.className = "palette-button";
            newCellButton.style.backgroundColor = 'white';
            newCellButton.onclick = () => changeColor(newCellButton.id);
            newCell.appendChild(newCellButton);
            newRow.appendChild(newCell);
        }
        t.appendChild(newRow);
    }

    palette.appendChild(t);
}


function readURL(input, page) {
    if (input.files && input.files[0]) {
        let reader = new FileReader();
        reader.onload = function (e) {
            let image = new Image();
            image.src = e.target.result;
            image.onload = function() {
                let image_tag;
                if (page === 'create-nft') {
                    image_tag = document.getElementById('id-nft-preview');
                    if (image_tag == null) {
                        image_tag = document.createElement('img');
                        let palette = document.getElementById('id-create-palette');
                        while (palette.hasChildNodes()) {
                            palette.removeChild(palette.firstChild);
                        }
                        palette.appendChild(image_tag);
                    }
                } else {
                    image_tag = document.getElementById('id-profile-preview');
                }

                image_tag.setAttribute('src', e.target.result);
                image_tag.setAttribute('height', IMAGE_FIX_HEIGHT);
                if (page === 'create-nft') {
                    let button_tag = document.getElementById('id-create-button');
                    button_tag.disabled = false;
                }
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function finalizeImage() {
    let palette = document.getElementById('id-create-nft-table');
    if (palette != null) {
        html2canvas(palette).then(function(canvas) {
        let image_data = canvas.toDataURL('image/png');
        let image_tag = document.createElement('img');
        image_tag.id = 'id-nft-preview';
        image_tag.setAttribute('src', image_data);
        while (palette.hasChildNodes()) {
            palette.removeChild(palette.firstChild);
        }
        palette.appendChild(image_tag);
        })
    }
}



function stuffing(a_id, a_et) {
    var id = a_id;
    var d = new Date(a_et * 1000); 
    // Set the date we're counting down to
    var countDownDate = new Date(d).getTime();
    // Get today's date and time
    var now = new Date().getTime();
  
    // Find the distance between now and the count down date
    var distance = countDownDate - now;
    // Time calculations for days, hours, minutes and seconds
    var days = Math.floor(distance / (1000 * 60 * 60 * 24));
    var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    var seconds = Math.floor((distance % (1000 * 60)) / 1000);
    var stuff = "countdown_" + id;
    // Display the result in the element with id="demo"
    document.getElementById(stuff).innerHTML = days + "d " + hours + "h "
    + minutes + "m " + seconds + "s ";
  
    // If the count down is finished, write some text 
    if (distance < 0) {
      //clearInterval(x);
      document.getElementById(stuff).innerHTML = "EXPIRED";
    }

  }

  function create_interval(f, a_id, a_et) {
    setInterval(function(){
        f(a_id, a_et);
    }, 1000)
  }


/* ajax code for get auctions
function getAuctions() {
    $.ajax({
        url: "/get-auctions",
        dataType : "json",
        success: displayAuctions,
    });
}

function displayAuctions() {

}

function sanitize(s) {
    // Replacing the ampersand first
    return s.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
}

function getCSRFToken() {
    let cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
        let c = cookies[i].trim()
        if (c.startsWith("csrftoken=")) {
            return c.substring("csrftoken=".length, c.length)
        }
    }
    return "unknown";
}

*/
function getDetails() {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (xhr.readyState != 4) return
        updatePage(xhr)
    }

    xhr.open("POST", getDetailsURL, true)
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    xhr.send("nft_id="+nft_id+"&csrfmiddlewaretoken="+csrfToken)
}

function updatePage(xhr) {
    if (xhr.status == 200) {
        let response = JSON.parse(xhr.responseText)
        updateDetails(response)
        return
    } 
    return
}

function updateDetails(response) {
    var highest_bid_field = document.getElementById("highest_bid_here")
    highest_bid_field.innerHTML = "Price: $" + response["highest_bid_price"] + "\nUser: " + response["first_name"] + " " + response["last_name"]
    var bid_count_field = document.getElementById("number_bids_here")
    bid_count_field.innerHTML = response["number_of_bids"]
    if (response["reload"]) {
        location.reload()
    }
}