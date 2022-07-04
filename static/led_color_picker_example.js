



async function addNetworks() {
    const response = await fetch('/ajax/ssids');
    const activeNetworks = await response.json();
    
    console.log("fetching...")
    var form = document.getElementById("form-creation")

    console.log("retrieved the following networks",activeNetworks["ssids"])

    console.log("Updating potential options")
    activeNetworks["ssids"].forEach(function (ssid, index) {

        console.log(ssid, index);

        var newNet = document.createElement("input")
        newNet.setAttribute("type","radio")
        newNet.setAttribute("name","ssid")
        newNet.setAttribute("id",index)
        newNet.setAttribute("value",ssid)

        var netLabel = document.createElement("label")
        netLabel.setAttribute("for",index)
        netLabel.innerHTML = ssid;
 
        var br = document.createElement("br")

        // form.appendChild(newNet)
        // form.appendChild(netLabel)
        // form.appendChild(br)
        form.prepend(newNet)
        form.prepend(netLabel)
        form.prepend(br)    
        // form.append(newNet)
        // form.append(netLabel)
        // form.prepend(br)


    });

}


async function submitNetwork() {
    
    console.log("Got the submission request!")
    ssid = document.querySelector('input[name="ssid"]:checked').value
    pass = document.getElementById("password").value;
    
    console.log("Entered password",pass)

    if (pass === "") {
        document.getElementById('passErr').innerHTML = "Please enter the correct password for the network"
        
    } else {
        document.getElementById('passErr').innerHTML = ""
    }

    netObj = {
        "ssid":ssid,
        "pass":pass
    }

    
    data = JSON.stringify(netObj);
    window.fetch("/setWifi", {
        method: "POST",
        body: data,
        headers: {
            'Content-Type': 'application/json; charset=utf-8',
        },
    }).then(response => {
        console.log("sucess!: " + response)
    }, error => {
        console.log("error!: " + error)
    })

}


