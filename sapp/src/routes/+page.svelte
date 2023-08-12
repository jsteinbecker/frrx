<script>
    import { onMount } from "svelte";

    async function fetchUserData() {
        const response = await fetch('http://127.0.0.1:8000/api/user/');
        const json = await response.json();
        const user = json.data.user;

        console.log(json); // This will log the user data once it's retrieved.
        return user;
    }

    var user;
 
    onMount(async () => {
        user = await fetchUserData();
    });

    </script>


    <h1>FlowRate</h1>
    <h3>Welcome, {user}.</h3>
    <div></div>

