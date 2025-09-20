import cv2
import av
import asyncio
import requests
from aiortc import RTCPeerConnection, RTCSessionDescription

WHEP_URL = "https://customer-de5fgahocfauk9ea.cloudflarestream.com/fc5cd217af19c699ba75808f9f150250/iframe"
async def run():
    pc = RTCPeerConnection()

    @pc.on("track")
    def on_track(track):
        print("Track received:", track.kind)
        if track.kind == "video":
            for frame in track.recv():
                img = frame.to_ndarray(format="bgr24")
                cv2.imshow("HexAir Drone Stream", img)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    # Create an SDP offer
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    # Send offer to Cloudflare WHEP endpoint
    response = requests.post(
        WHEP_URL,
        data=offer.sdp,
        headers={"Content-Type": "application/sdp"}
    )

    # Get back the SDP answer
    answer = RTCSessionDescription(sdp=response.text, type="answer")
    await pc.setRemoteDescription(answer)

    # Keep connection alive
    await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(run())
