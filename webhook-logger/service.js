const express = require("express");
const axios = require("axios");
const cors = require("cors");

const app = express();
const PORT = process.env.PORT || 8000;

const allowedOrigins = [
  "https://telex.im",
  "https://staging.telex.im",
  "https://telextest.im",
  "https://staging.telextest.im",
];

app.use(
  cors({
    origin: (origin, callback) => {
      if (!origin || allowedOrigins.includes(origin)) {
        callback(null, true);
      } else {
        callback(new Error("Not allowed by CORS"));
      }
    },
    credentials: true,
  })
);

app.use(express.json());

app.get("/integration.json", (req, res) => {
  const baseUrl = `${req.protocol}://${req.get("host")}`;
  const integration = {
    data: {
      date: {
        created_at: "2025-02-09",
        updated_at: "2025-02-09",
      },
      descriptions: {
        app_name: "Webhook Slug Logger",
        app_description: "Logs payloads to a webhook URL defined by a slug.",
        app_logo: "https://i.imgur.com/bRoRB1Y.png",
        app_url: baseUrl,
        background_color: "#fff",
      },
      is_active: true,
      integration_type: "output",
      key_features: ["- Logs payloads to webhook.site or any webhook endpoint"],
      category: "Logging",
      author: "Osinachi Chukwujama",
      website: baseUrl,
      settings: [
        {
          label: "webhook-slug",
          type: "text",
          required: true,
          default: "",
        },
      ],
      target_url: `${baseUrl}/target_url`,
    },
  };

  res.json(integration);
});

app.post("/target_url", async (req, res) => {
  const { message, settings } = req.body;
  const slug = settings?.["webhook-slug"];

  if (!slug) {
    return res.status(400).json({ error: "webhook-slug setting is required" });
  }

  const webhookUrl = `https://webhook.site/${slug}`;

  try {
    const response = await axios.post(
      webhookUrl,
      { message },
      {
        headers: { "Content-Type": "application/json" },
      }
    );

    res.json({ status: "success", webhookResponse: response.data });
  } catch (error) {
    console.error("Failed to send webhook:", error.message);
    res.status(500).json({ error: "Failed to send webhook" });
  }
});

app.listen(PORT, () => {
  console.log(`Webhook Slug Logger is running on port ${PORT}`);
});
