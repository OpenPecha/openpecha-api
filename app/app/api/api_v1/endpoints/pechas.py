from logging import currentframe
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from openpecha.core.layer import Layer, LayersEnum
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.services.pechas import (
    create_editor_content_from_pecha,
    create_export,
    create_opf_pecha,
    get_pecha,
    update_base_layer,
    update_pecha_with_editor_content,
)

router = APIRouter()


@router.get("", response_model=List[schemas.pecha.Pecha])
async def read_pecha(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.user.User = Depends(deps.get_current_user),
):
    """
    Retrieve pechas.
    """
    if crud.user.is_superuser(current_user):
        pechas = crud.item.get_multi(db, skip=skip, limit=limit)
    else:
        pechas = crud.pecha.get_multi_by_owner(
            db=db, owner_id=current_user.id, skip=skip, limit=limit
        )
    return pechas


@router.post("")
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
    current_user: schemas.user.User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """
    Create new pecha
    """
    pecha_id, front_cover_image_fn = await create_opf_pecha(
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
    pecha_obj = {
        "id": pecha_id,
        "title": title,
        "img": f"https://github.com/OpenPecha/{pecha_id}/raw/master/{pecha_id}.opf/assets/image/{front_cover_image_fn.name}",
    }
    pecha = crud.pecha.create_with_owner(
        db=db, obj_in=pecha_obj, owner_id=current_user.id
    )
    return {"pecha_id": pecha_id}


@router.get("/{pecha_id}/components", response_model=Dict[str, List[LayersEnum]])
def read_components(pecha_id: str):
    pecha = get_pecha(pecha_id)
    return pecha.components


@router.get("/{pecha_id}/base/{base_name}", response_model=str)
def read_base(pecha_id: str, base_name):
    pecha = get_pecha(pecha_id)
    return pecha.get_base(base_name)


@router.post("/{pecha_id}/base/{base_name}", status_code=status.HTTP_201_CREATED)
def create_base(
    pecha_id: str,
    base_name: str,
    base: schemas.pecha.BaseLayer,
    user: schemas.user.User = Depends(deps.get_current_user),
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
    updated_base: schemas.pecha.BaseLayer,
    layers: List[Layer],
    user: schemas.user.User = Depends(deps.get_current_user),
):
    """
    Update base and corresponding layers also updated.
    """
    updated_layers = update_base_layer(
        pecha_id, base_name, updated_base.content, list(map(lambda x: x.dict(), layers))
    )
    return {"base": updated_base.content, "layers": updated_layers}


@router.delete("/{pecha_id}/base/{base_name}", response_model=str)
def delete_base(
    pecha_id: str,
    base_name: str,
    user: schemas.user.User = Depends(deps.get_current_user),
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
    user: schemas.user.User = Depends(deps.get_current_user),
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
    user: schemas.user.User = Depends(deps.get_current_user),
):
    pecha = get_pecha(pecha_id)
    pecha.save_layer(base_name, layer_name, layer)
    return {"success": True}


@router.delete("/{pecha_id}/layers/{base_name}/{layer_name}", response_model=Layer)
def delete_layer(
    pecha_id: str,
    base_name: str,
    layer_name,
    user: schemas.user.User = Depends(deps.get_current_user),
):
    raise HTTPException(status_code=501, detail="Endpoint not functional yet")


@router.get("/{pecha_id}/export/{branch}")
def export_pecha(
    pecha_id: str,
    branch: str = "master",
    user: schemas.user.User = Depends(deps.get_current_user),
):
    download_link = create_export(pecha_id, branch)
    return {"download_link": download_link}


@router.get("/{pecha_id}/{base_name}/editor")
def get_editor_content(
    pecha_id: str,
    base_name: str,
    user: schemas.user.User = Depends(deps.get_current_user),
):
    return {"content": create_editor_content_from_pecha(pecha_id, base_name)}


@router.put("/{pecha_id}/{base_name}/editor")
def update_pecha(
    pecha_id: str,
    base_name: str,
    editor_content: schemas.pecha.EditorContent,
    user: schemas.user.User = Depends(deps.get_current_user),
):
    # try:
    update_pecha_with_editor_content(pecha_id, base_name, editor_content.content)
    # except Exception as e:
    #     print(e)
    #     return {"success": False}
    return {"success": True}
