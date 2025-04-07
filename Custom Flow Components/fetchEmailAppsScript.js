function sendUnreadEmailsToS3() {
  const threads = GmailApp.search('is:unread label:inbox');
  const apiUrl = 'https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/store-email'; // Replace with your endpoint
  const apiKey = 'YOUR_API_KEY'; // Optional: only if your API requires it

  for (let i = 0; i < threads.length; i++) {
    const messages = threads[i].getMessages();

    for (let j = 0; j < messages.length; j++) {
      const msg = messages[j];
      const emailData = {
        subject: msg.getSubject(),
        from: msg.getFrom(),
        body: msg.getPlainBody(),
        date: msg.getDate().toISOString()
      };

      // Optional: Add delay if you want to space them out
      Utilities.sleep(3000); // Wait 3 seconds per email

      // Send the email to Lambda via POST request
      try {
        const response = UrlFetchApp.fetch(apiUrl, {
          method: 'post',
          contentType: 'application/json',
          payload: JSON.stringify(emailData),
          headers: {
            'x-api-key': apiKey  // Remove this line if not using an API key
          },
          muteHttpExceptions: true
        });

        Logger.log(`Sent email: ${emailData.subject}`);
        Logger.log(`Response: ${response.getContentText()}`);
      } catch (e) {
        Logger.log(`Failed to send email: ${e}`);
      }
    }

    // Mark the whole thread as read after processing all messages
    threads[i].markRead();
  }
}
