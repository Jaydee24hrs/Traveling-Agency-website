function makePayment() {
    FlutterwaveCheckout({
        public_key: "FLWPUBK_TEST-02b9b5fc6406bd4a41c3ff141cc45e93-X",
        tx_ref: "txref-DI0NzMx13",
        amount: 2500,
        currency: "NGN",
        payment_options: "card, banktransfer, ussd",
        meta: {
            source: "docs-inline-test",
            consumer_mac: "92a3-912ba-1192a",
        },
        redirect_url: "http://localhost:8000/",
        customer: {
            email: "test@mailinator.com",
            phone_number: "08100000000",
            name: "Ayomide Jimi-Oni",
        },
        customizations: {
            title: "Flutterwave Developers",
            description: "Test Payment",
            logo: "https://checkout.flutterwave.com/assets/img/rave-logo.png",
        },
        callback: function (data) {
            if (data.status === "successful") {
                console.log("payment successful");
                window.location.href = "/";
            } else {
                console.log("payment failed or incomplete: ", data);
                alert("payment was not successful. Please try again");
            }
        },
        onclose: function () {
            console.log("Payment cancelled!");
            alert("Payment was cancelled.");
        }
    });
}
