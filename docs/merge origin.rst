Diff with original
==================

This page list the difference after happypanda last release (1.1) out.

In generel here is the difference.

* import sorting
* one line per import
* use relative import.

Main Module
--------------

* Main function. current_exit_code is still `0` but it is set as :data:`happypanda.app_constants.APP_RESTART_CODE`.
* :py:obj:`happypanda.__main__.program`

 * change in __init__ of AppWindow

   * add login_check_invoker attribute.
   * add check_site_logins method.

     * LoginCheck class is moved to its own file (check_login_obj).

       * the filename is based on convention (underscore splitted words and added obj for QObject)
       * the class also add `Object` for convention.

   * several method execution on `__init__` is splitter for better viewing.
     Also reordering the execution, so it is grouped better (e.g. db_startup attribute is
     initiated after _db_startup_thread.start method executed.)
   * initUI method is changed to init_ui.

 * change in set_shortcuts method

   * QShortcut is not set to a variable, as the variable will not be used anywhere and will raise
     pep8 error
   * change to apply pep8 (shorter line lengths)

 * change in init_watchers method.

   * remove_gallery inner function is moved to class method (_remove_gallery)
   * update_gallery inner function is moved to class method (_update_gallery)
   * created inner function is moved using lambda
   * modified inner function is moved using lambda
   * moved inner function is moved to class method (_watcher_moved)
   * deleted inner function is moved to class method (_watcher_deleted)

 * change in startup method

   * normalize_first_time inner function is moved to class method (normalize_first_time)
   * done inner function is moved to class method (_startup_done)
     * Abandomnent message removed.
   * old method when checkingapp_constants.FIRST_TIME_LEVEL is kept there.

 * change in init_ui method

   * initUI method is changed to init_ui (stated on __init__ changes)
   * refresh_view inner function is moved using lambda
   * code between `Create statusbar: OK` and `Create system tray: OK` is moved to
     create_system_tray method. tray_icon inner function is moved to class method (inner_function)
   * code between `Create system tray: OK` and `Show window: OK` is moved to
     show_window method. The content is modified to follow the current commit.

 * change in init_ui method

   * upd_chk inner class is moved to its own file (update_checker_obj)

     * the filename is based on convention (underscore splitted words and added obj for QObject)
     * the class name is changed from upd_chk to UpdateCheckerObject for convention

   * check_update inner_function is moved to class method (_check_update_func)

 * change in get_metadata method.

   * code between fetch_instance variable initiation and setting fetch_instance's galleries
     attribute is move to get_metadata_gallery method. If-else loop is simplified.
   * done inner function is moved to _get_metadata_done method.

     * added fetch_instance to link fetch_instance from function to method
     * GalleryContextMenu inner class on done function is moved to its own file
       (gallery_context_menu). app_instance parameter is added to link app instance to class

 * change in init_toolbar method. inner function is moved to its own method.
