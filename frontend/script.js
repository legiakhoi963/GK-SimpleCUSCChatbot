document.addEventListener("DOMContentLoaded", () => {
    const chatbotToggler = document.querySelector(".chatbot-toggler");
    const closeBtn = document.querySelector(".close-btn");
    const chatbox = document.querySelector(".chatbox");
    const chatInput = document.querySelector(".chat-input textarea");
    const sendChatBtn = document.querySelector(".chat-input span");
  
    // BONUS CODE
    const userInfoForm = document.getElementById("userInfoForm");
    const userInfoFormContainer = document.getElementById(
      "userInfoFormContainer"
    );
    const chatboxContainer = document.getElementById("chatbox");
    const chatInputContainer = document.querySelector(".chat-input");
    //
  
    let session_id = null;
    let userMessage = null;
    const inputInitHeight = chatInput.scrollHeight;
  
    const createChatLi = (message, className) => {
      // Create a chat <li> element with passed message and className
      const chatLi = document.createElement("li");
      chatLi.classList.add("chat", `${className}`);
      let chatContent =
        className === "outgoing"
          ? `<p></p>`
          : `<span class="material-symbols-outlined">smart_toy</span><p></p>`;
      chatLi.innerHTML = chatContent;
      chatLi.querySelector("p").textContent = message;
      return chatLi; // return chat <li> element
    };
  
    const generateResponse = (chatElement) => {
      const API_URL = "http://localhost:8000/chat";
      const messageElement = chatElement.querySelector("p");
  
      // Define the properties and message for the API request
      const requestOptions = {
        method: "POST",
        headers: {
          accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: session_id,
          chat_request: userMessage,
        }),
      };
  
      // Send POST request to API, get response and set the reponse as paragraph text
      fetch(API_URL, requestOptions)
        .then((res) => res.json())
        .then((data) => {
          messageElement.textContent = data.chat_response;
        })
        .catch(() => {
          messageElement.classList.add("error");
          messageElement.textContent =
            "Xin lỗi! Hệ thống đang gặp sự cố. Bạn vui lòng thử lại sau.";
        })
        .finally(() => chatbox.scrollTo(0, chatbox.scrollHeight));
    };
  
    const handleChat = () => {
      userMessage = chatInput.value.trim(); // Get user entered message and remove extra whitespace
      if (!userMessage) return;
  
      // Clear the input textarea and set its height to default
      chatInput.value = "";
      chatInput.style.height = `${inputInitHeight}px`;
  
      // Append the user's message to the chatbox
      chatbox.appendChild(createChatLi(userMessage, "outgoing"));
      chatbox.scrollTo(0, chatbox.scrollHeight);
  
      setTimeout(() => {
        // Display "Thinking..." message while waiting for the response
        const incomingChatLi = createChatLi("...", "incoming");
        chatbox.appendChild(incomingChatLi);
        chatbox.scrollTo(0, chatbox.scrollHeight);
        generateResponse(incomingChatLi);
      }, 600);
    };
  
    chatInput.addEventListener("input", () => {
      // Adjust the height of the input textarea based on its content
      chatInput.style.height = `${inputInitHeight}px`;
      chatInput.style.height = `${chatInput.scrollHeight}px`;
    });
  
    chatInput.addEventListener("keydown", (e) => {
      // If Enter key is pressed without Shift key and the window
      // width is greater than 800px, handle the chat
      if (e.key === "Enter" && !e.shiftKey && window.innerWidth > 800) {
        e.preventDefault();
        handleChat();
      }
    });
  
    sendChatBtn.addEventListener("click", handleChat);
    // BONUS CODE
    closeBtn.addEventListener("click", () =>
      document.body.classList.remove("show-chatbot")
    );
    chatbotToggler.addEventListener("click", () =>
      document.body.classList.toggle("show-chatbot")
    );
    //
  
    //   closeBtn.addEventListener("click", () =>
    //     document.body.classList.remove("show-chatbot")
    //   );
    //   chatbotToggler.addEventListener("click", () =>
    //     document.body.classList.toggle("show-chatbot")
    //   );
  
    // Xử lý gửi biểu mẫu thông tin người dùng
    userInfoForm.addEventListener("submit", async (event) => {
      event.preventDefault();
  
      const name = document.getElementById("name").value;
      const phone = document.getElementById("phone").value;
      const email = document.getElementById("email").value;
      const address = document.getElementById("address").value;
  
      const userInfo = { name, phone, email, address };
      session_id = email; // Lưu trữ email của người dùng làm session ID
      console.log("session_id ", session_id);
      console.log(name, phone, email, address);
      try {
        const response = await fetch("http://localhost:8000/user_info", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(userInfo),
        });
  
        if (response.ok) {
          // Ẩn biểu mẫu thông tin người dùng và hiển thị giao diện trò chuyện
          userInfoFormContainer.style.display = "none";
          chatboxContainer.style.display = "block";
          chatInputContainer.style.display = "flex";
        } else {
          alert("Gửi thông tin không thành công. Vui lòng thử lại.");
        }
      } catch (error) {
        console.error("Error:", error);
        alert("Đã xảy ra lỗi khi gửi thông tin của bạn. Vui lòng thử lại.");
      }
    });
  });
  