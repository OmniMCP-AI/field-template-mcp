
``` python

class UpdateRangeRequest(BaseModel):
    spreadsheet_id: str = Field(description="Google Sheets document ID")
    worksheet: WorkSheetInfo = Field(description="Worksheet Info")
    range: str = Field(
        description="Cell range in A1 notation. Use complete A1 notation with explicit start and end cells (e.g., A1:B10). Avoid incomplete formats like A:B or 1:5."
    )
    values: list[list[Any]] = Field(description="The values to update as 2D array")
    create_new_on_permission_error: Optional[bool] = Field(
        default=True, 
        description="If True, create a new spreadsheet when permission denied. If False, raise error on permission issues."
    )


@router.post("/update")
async def update_range(
    request: UpdateRangeRequest, api_request: Request
) -> UpdateRangeResponse:
    """
    <description>Overwrites cell values in a specified range with provided 2D array data. Replaces existing content completely - does not merge or append data.</description>

    <use_case>Use for bulk data updates, replacing table contents, or writing processed results back to sheets. Efficient for updating structured data blocks.</use_case>

    <limitation>Data array dimensions must exactly match range size. Cannot update non-contiguous ranges. Overwrites formulas and formatting. Maximum 25,000 cells per update.</limitation>

    <failure_cases>Fails if data dimensions don't match range or range exceeds sheet bounds. Partial updates may occur on network interruption. Data truncation on cells >50,000 characters.</failure_cases>
    """
    try:
        user_id = api_request.headers.get("user-id")
        task_id = api_request.headers.get("task-id")
        clear_contextvars()
        _ = bind_contextvars(task_id=task_id)
        if not user_id:
            raise UserError("user-id is required")
        return await service.update_range(request, user_id)
    except Exception as e:
        logger.error(f"Error updating range: {e}", traceback=traceback.format_exc())
        raise UserError(f"Error updating range: {e}")
```
