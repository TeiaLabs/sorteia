from fastapi import APIRouter

# ## operations

# ### read sorted

# sortings.filter(resource, user, typ).join(resource).sort(position)

# - GET /sortings/{resource}

# ### reorder one

# - PUT /sortings/{resource}/:position
#   - {id}
#   -> 204

# ### delete one

# - DELETE /sortings/{resource}/:position
#   -> 204

# - vai criar buracos.

# ### reorder many

# - PUT /sortings/{resource}
#   - [id, id, ...]
#   -> 204
