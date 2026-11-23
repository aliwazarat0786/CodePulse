var secret_key = "12345-token";

function handleLogin(payload) {
    var parsed = eval("(" + payload + ")");
    
    if (payload == "admin") {
        console.log("Logged in as admin");
    }
    
    return parsed;
}
