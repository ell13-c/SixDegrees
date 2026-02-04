<!-- 
PROFILE PAGE - personal profile other users will see
TODO: Fix AWFUL Formatting
TODO: Add option to relevant sections for users to edit its content (when it is their own)
TODO: Link relevant sections to supabase
--> 

<template>
    <div class="page-container">
        <div id="main-profile-box">
            <div class="profile-picture-container">         
                <img id="profile-pic" src="./Assets/TempUserPhoto.png" alt="Undefined User Photo">
                <div id="friends-box">
                    <button type="button" id="friends-btn">
                        Friends
                    </button>
                </div>
            </div>
            <div class="bio-container">
                <p id="profile-name">User Name</p>
                <p id="bio">User background. Whatever they think is intereting about themselves.</p>
            </div>
        </div>
        <div id="hobbies-box">
            <ul>
                <li>Hobby 1</li>
                <li>Hobby 2</li>
                <li>Hobby 3</li>
                <li>Hobby 4</li>
            </ul>
        </div>
    </div>
</template>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #1a1a1a;
}

#main-profile-box {
  display: flex;
  background: #2d2d2d;
  padding: 2vw;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  width: 100%;
}

.profile-picture-container {
  display: flex;
  flex-direction: column;
  background: #2d2d2d;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  height: 25%;
  max-height: 400px;
  aspect-ratio: 1;
  object-fit: cover;
}

#profile-pic {
  object-fit: scale-down;
  max-width: 50%;
  max-height: 50%;
}

#friends-box {
  background: #2d2d2d;
  width: 100%;
}

#profile-name {
  font-weight: bolder;
}

#hobbies-box {
  background: #2d2d2d;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  width: 100%;
  max-width: 400px;
  align-items: center;
  justify-items: center;
}

p,ul {
  color: #fff;
}
</style>