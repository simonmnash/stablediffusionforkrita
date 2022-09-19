from fastapi import FastAPI, File, UploadFile, HTTPException, Security, Depends, WebSocket
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security.api_key import APIKeyHeader
import config
from functools import lru_cache
from pydantic import BaseModel
import torch
from alteredpipeline import StableDiffusionPipelineAltered
from img2img import StableDiffusionImg2ImgPipeline
import uuid
import base64
import io
from PIL import Image
api_key_header_auth = APIKeyHeader(name='x-api-key')

@lru_cache()
def get_settings():
    return config.Settings()

async def get_api_key(api_key_header: str = Security(api_key_header_auth), settings: config.Settings = Depends(get_settings)):
    if api_key_header != settings.api_key:
        raise HTTPException(
            status_code= 401,
            detail="Invalid API Key",
        )
    else:
        return api_key_header

app = FastAPI(dependencies=[Depends(get_api_key)])
settings = get_settings()
IMAGEDIR = 'files/'
text_to_image_pipe = StableDiffusionPipelineAltered.from_pretrained("CompVis/stable-diffusion-v1-4",
                                                    use_auth_token=settings.huggingface_token,
                                                    )

image_to_image_pipe = StableDiffusionImg2ImgPipeline.from_pretrained("CompVis/stable-diffusion-v1-4",
                                                    use_auth_token=settings.huggingface_token,
                                                    )


class PromptData(BaseModel):
    prompt: str
    width: int
    height: int


@app.post("/prompt_to_image", dependencies=[Depends(get_api_key)])
async def newlayer(data: PromptData):
    print(data)
    output = text_to_image_pipe(data.prompt, data.width, data.height, 20)
    image = output["sample"][0]
    file_name = f"{IMAGEDIR}{uuid.uuid4().hex}_{data.width}_{data.height}.png"
    image.save(file_name)
    return FileResponse(f'{file_name}')


@app.post("/image_to_image", dependencies=[Depends(get_api_key)])
async def newlayerfromimage(data: PromptData):
    '''
    Stub method awaiting image upload implementation.
    '''
    img = Image(size=(data.width, data.height))
    output = image_to_image_pipe(img, data.prompt, data.width, data.height, 2)
    image = output["sample"][0]
    file_name = f"{IMAGEDIR}{uuid.uuid4().hex}_{data.width}_{data.height}.png"
    image.save(file_name)
    return FileResponse(f'{file_name}')
