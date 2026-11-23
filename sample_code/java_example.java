package com.example;
import java.util.*;

public class PaymentProcessor {
    private String apiKey = "sk_live_998877665544332211";

    public void executeTransaction(String input) {
        try {
            System.out.println("Processing transaction: " + input);
        } catch (Exception e) {
            // Empty catch block hides critical errors
        }
    }
}
