import subprocess
import time


class DenoRuntime:
    def __init__(self, js_code: str) -> None:
        """
        Initialize the Deno runtime wrapper.

        Args:
            js_code: The JavaScript source code containing the logic to solve.
        """
        # We wrap the JS code to handle input from Deno.args
        self.script_template: str = f"""
        {js_code}
        
        try {{
            // Deno.args[0] is the first command line argument passed
            const input = Deno.args[0]; 
            
            // Assuming the function is named 'solve'
            const result = solve(input);
            
            console.log(result);
        }} catch (e) {{
            console.error(e);
            Deno.exit(1);
        }}
        """

    def call(self, argument: str | int) -> str:
        """
        Execute the stored JS script with a specific argument.

        Args:
            argument: The seed or input data (string or integer).

        Returns:
            The standard output from the Deno process as a string.
        """
        # In Python 3.9+, 'list[str]' is preferred over 'List[str]'
        cmd: list[str] = ["deno", "run", "-", str(argument)]

        try:
            process: subprocess.CompletedProcess[str] = subprocess.run(
                cmd,
                input=self.script_template,
                capture_output=True,
                text=True,
                check=False,  # We manually check returncode below
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Deno executable not found. Is it installed and in your PATH?"
            )

        if process.returncode != 0:
            raise RuntimeError(f"Deno Error: {process.stderr.strip()}")

        return process.stdout.strip()


# --- USAGE EXAMPLE ---

if __name__ == "__main__":
    # Your extracted logic
    extracted_js: str = r"""
    let keyFragments = ["4Z7lUo", "gwIVSMD", "PLmz2elE2v", "Z4OFV0", "SZ6RZq6Zc", "zhJEFYxrz8", "FOm7b0", "axHS3q4KDq", "o9zuXQ", "4Aebt", "wgjjWwKKx", "rY4VIxqSN", "kfjbnSo", "2DyrFA1M", "YUixDM9B", "JQvgEj0", "mcuFx6JIek", "eoTKe26gL", "qaI9EVO1rB", "0xl33btZL", "1fszuAU", "a7jnHzst6P", "wQuJkX", "cBNhTJlEOf", "KNcFWhDvgT", "XipDGjST", "PCZJlbHoyt", "2AYnMZkqd", "HIpJh", "KH0C3iztrG", "W81hjts92", "rJhAT", "NON7LKoMQ", "NMdY3nsKzI", "t4En5v", "Qq5cOQ9H", "Y9nwrp", "VX5FYVfsf", "cE5SJG", "x1vj1", "HegbLe", "zJ3nmt4OA", "gt7rxW57dq", "clIE9b", "jyJ9g", "B5jXjMCSx", "cOzZBZTV", "FTXGy", "Dfh1q1", "ny9jqZ2POI", "X2NnMn", "MBtoyD", "qz4Ilys7wB", "68lbOMye", "3YUJnmxp", "1fv5Imona", "PlfvvXD7mA", "ZarKfHCaPR", "owORnX", "dQP1YU", "dVdkx", "qgiK0E", "cx9wQ", "5F9bGa", "7UjkKrp", "Yvhrj", "wYXez5Dg3", "pG4GMU", "MwMAu", "rFRD5wlM", ];

let solve = (function(tmdbId) {
    if (void 0 === tmdbId)
        return "rive";
    try {
        let t, n;
        let r = String(tmdbId);
        if (isNaN(Number(tmdbId))) {
            let e = r.split("").reduce( (e, t) => e + t.charCodeAt(0), 0);
            ((t = keyFragments[e % keyFragments.length] || btoa(r)),
            (n = Math.floor((e % r.length) / 2)));
        } else {
            let i = Number(tmdbId);
            ((t = keyFragments[i % keyFragments.length] || btoa(r)),
            (n = Math.floor((i % r.length) / 2)));
        }
        let i = r.slice(0, n) + t + r.slice(n)
          , output = (function(e) {
            let t = String(e)
              , n = 3735928559 ^ t.length;
            for (let e = 0; e < t.length; e++) {
                let r = t.charCodeAt(e);
                ((r ^= ((131 * e + 89) ^ (r << (e % 5))) & 255),
                (n = (((n << 7) | (n >>> 25)) >>> 0) ^ r));
                let i = (65535 & n) * 60205
                  , o = ((n >>> 16) * 60205) << 16;
                ((n = (i + o) >>> 0),
                (n ^= n >>> 11));
            }
            return ((n ^= n >>> 15),
            (n = ((65535 & n) * 49842 + (((n >>> 16) * 49842) << 16)) >>> 0),
            (n ^= n >>> 13),
            (n = ((65535 & n) * 40503 + (((n >>> 16) * 40503) << 16)) >>> 0),
            (n ^= n >>> 16),
            (n = ((65535 & n) * 10196 + (((n >>> 16) * 10196) << 16)) >>> 0),
            (n ^= n >>> 15).toString(16).padStart(8, "0"));
        }
        )((function(e) {
            e = String(e);
            let t = 0;
            for (let n = 0; n < e.length; n++) {
                let r = e.charCodeAt(n)
                  , i = (((t = (r + (t << 6) + (t << 16) - t) >>> 0) << (n % 5)) | (t >>> (32 - (n % 5)))) >>> 0;
                ((t ^= (i ^ ((r << (n % 7)) | (r >>> (8 - (n % 7))))) >>> 0),
                (t = (t + ((t >>> 11) ^ (t << 3))) >>> 0));
            }
            return ((t ^= t >>> 15),
            (t = ((65535 & t) * 49842 + ((((t >>> 16) * 49842) & 65535) << 16)) >>> 0),
            (t ^= t >>> 13),
            (t = ((65535 & t) * 40503 + ((((t >>> 16) * 40503) & 65535) << 16)) >>> 0),
            (t ^= t >>> 16).toString(16).padStart(8, "0"));
        }
        )(i), );
        let finalKey = btoa(output);
        return finalKey;
    } catch (e) {
        return "topSecret";
    }
}
)

    """

    try:
        runtime: DenoRuntime = DenoRuntime(extracted_js)
        # We can pass an int or a str now, thanks to the type hint and str() conversion
        start_time = time.perf_counter()
        result: str = runtime.call(1418)
        end_time = time.perf_counter()
        print(f"Secret Key: {result}")
        print(f"Execution time: {end_time - start_time:.6f} seconds")
    except RuntimeError as e:
        print(f"Failed: {e}")
