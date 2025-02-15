package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strings"
)

// Message represents the incoming payload structure
type Message struct {
	ChannelID string    `json:"channel_id"`
	Settings  []Setting `json:"settings"`
	Message   string    `json:"message"`
}

type Setting struct {
	Label       string   `json:"label"`
	Type        string   `json:"type"`
	Description string   `json:"description"`
	Required    bool     `json:"required"`
	Default     any      `json:"default"`
	Options     []string `json:"options"`
}

// settingsProcessing applies the settings to the message
func settingsProcessing(msgReq Message) string {
	maxMessageLength := 500
	var repeatWords []string
	noOfRepetitions := 1

	// Extract settings
	for _, setting := range msgReq.Settings {
		switch setting.Label {
		case "maxMessageLength":
			if val, ok := setting.Default.(float64); ok {
				maxMessageLength = int(val)
			}
		case "repeatWords":
			if val, ok := setting.Default.(string); ok {
				repeatWords = strings.Split(val, ", ")
			}
		case "noOfRepetitions":
			if val, ok := setting.Default.(float64); ok {
				noOfRepetitions = int(val)
			}
		}
	}

	formattedMessage := msgReq.Message

	// Repeat specified words
	for _, word := range repeatWords {
		formattedMessage = strings.ReplaceAll(formattedMessage, word, strings.Repeat(word+" ", noOfRepetitions))
	}
	// Apply maxMessageLength constraint
	if len(formattedMessage) > maxMessageLength {
		formattedMessage = formattedMessage[:maxMessageLength]
	}

	return formattedMessage
}

func handleIncomingMessage(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	var msgReq Message
	if err := json.NewDecoder(r.Body).Decode(&msgReq); err != nil {
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}

	formattedMessage := settingsProcessing(msgReq)
	log.Printf("Formatted message: %s", formattedMessage)

	response := map[string]string{
		"event_name": "message_formatted",
		"message":    formattedMessage,
		"status":     "success",
		"username":   "message-formatter-bot",
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func handleFormatterJSON(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	//read the json file
	byteValue, err := os.ReadFile("formatter.json")
	if err != nil {
		http.Error(w, "Failed to read file", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Write(byteValue)
}

func enableCORS(handler http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Set CORS headers
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

		// Handle preflight requests
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		handler(w, r)
	}
}

func main() {
	http.HandleFunc("/format-message", enableCORS(handleIncomingMessage))
	http.HandleFunc("/formatter-json", enableCORS(handleFormatterJSON))
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	log.Printf("Server running on port %s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
