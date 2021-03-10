from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from openpecha.core.layer import Layer, LayersEnum

from app import schemas
from app.api import deps
from app.services.pechas import (
    create_export,
    create_opf_pecha,
    get_pecha,
    update_base_layer,
)
from app.services.text_obj.texts import get_text_obj

router = APIRouter()


@router.post("/")
async def create_pecha(
    title: str,
    author: str,
    sku: str,
    subtitle: Optional[str] = "",
    collection: Optional[str] = "",
    publisher: Optional[str] = "",
    text_file: UploadFile = File(...),
    front_cover_image: UploadFile = File(...),
    publication_data_image: UploadFile = File(...),
):
    """
    Create new pecha
    """
    pecha_id = await create_opf_pecha(
        text_file,
        title,
        subtitle,
        author,
        collection,
        publisher,
        sku,
        front_cover_image,
        publication_data_image,
    )
    return {"pecha_id": pecha_id}


@router.get("/{pecha_id}/components", response_model=Dict[str, List[LayersEnum]])
def read_components(pecha_id: str):
    pecha = get_pecha(pecha_id)
    return pecha.components


@router.get("/{pecha_id}/texts/{text_id}", response_model=schemas.Text)
def read_text(pecha_id: str, text_id: str, page_no: Optional[int] = None):
    """
    Redrieve text of the pecha
    """
    text = get_text_obj(pecha_id, text_id)
    return text


@router.get("/{pecha_id}/base/{base_name}", response_model=str)
def read_base(pecha_id: str, base_name):
    pecha = get_pecha(pecha_id)
    return pecha.get_base(base_name)


@router.post("/{pecha_id}/base/{base_name}", status_code=status.HTTP_201_CREATED)
def create_base(
    pecha_id: str,
    base_name: str,
    base: schemas.core.BaseLayer,
    user: schemas.core.User = Depends(deps.get_user),
):
    """
    Create new base layer.
    """
    pecha = get_pecha(pecha_id)
    pecha.base[base_name] = base.content
    pecha.save_base()
    return {"success": True}


@router.put("/{pecha_id}/base/{base_name}")
def update_base(
    pecha_id: str,
    base_name: str,
    updated_base: schemas.core.BaseLayer,
    layers: List[schemas.core.AnnLayer],
    user: schemas.core.User = Depends(deps.get_user),
):
    """
    Update base and corresponding layers also updated.
    """
    updated_layers = update_base_layer(
        pecha_id,
        updated_base.id,
        updated_base.content,
        list(map(lambda x: x.dict(), layers)),
    )
    return updated_base, updated_layers


@router.delete("/{pecha_id}/base/{base_name}", response_model=str)
def delete_base(
    pecha_id: str, base_name: str, user: schemas.core.User = Depends(deps.get_user)
):
    raise HTTPException(status_code=501, detail="Endpoint not functional yet")


@router.get("/{pecha_id}/layers/{base_name}", response_model=List[Layer])
def read_layers(pecha_id: str, base_name: str):
    raise HTTPException(status_code=501, detail="Endpoint not functional yet")


@router.get("/{pecha_id}/layers/{base_name}/{layer_name}", response_model=Layer)
def read_layer(pecha_id: str, base_name, layer_name: str):
    pecha = get_pecha(pecha_id)
    return pecha.get_layer(base_name, LayersEnum(layer_name))


@router.post("/{pecha_id}/layers/{base_name}/{layer_name}", response_model=Layer)
def create_layer(
    pecha_id: str,
    base_name: str,
    layer_name: str,
    layer: Layer,
    user: schemas.core.User = Depends(deps.get_user),
):
    pecha = get_pecha(pecha_id)
    pecha.layers[base_name][LayersEnum(layer_name)] = layer
    pecha.save_layers()
    return {"success": True}


@router.put("/{pecha_id}/layers/{base_name}/{layer_name}")
def update_layer(
    pecha_id: str,
    base_name,
    layer_name: str,
    layer: Layer,
    user: schemas.core.User = Depends(deps.get_user),
):
    print(user)
    pecha = get_pecha(pecha_id)
    pecha.layers[base_name][LayersEnum(layer_name)] = layer
    pecha.save_layers()
    return {"success": True}


@router.delete("/{pecha_id}/layers/{base_name}/{layer_name}", response_model=Layer)
def delete_layer(
    pecha_id: str,
    base_name: str,
    layer_name,
    user: schemas.core.User = Depends(deps.get_user),
):
    raise HTTPException(status_code=501, detail="Endpoint not functional yet")


@router.get("/{pecha_id}/export/{branch}")
def export_pecha(
    pecha_id: str,
    branch: str = "master",
    user: schemas.core.User = Depends(deps.get_user),
):
    download_link = create_export(pecha_id, branch)
    return {"download_link": download_link}